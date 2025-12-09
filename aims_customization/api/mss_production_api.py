# aims_customization/api/mss_production_api.py
from __future__ import annotations
import json
from datetime import datetime
import frappe

def safe(val): return val if val not in (None, "") else ""

def _month_str_from_date(dt):
    if not dt: return ""
    if isinstance(dt, str):
        try: dt = datetime.strptime(dt, "%Y-%m-%d")
        except Exception: return ""
    return dt.strftime("%b-%y")

@frappe.whitelist()
def get_sales_orders(search_text=None, month=None, customer=None, limit=500):
    params = []
    sql = """SELECT name, customer, customer_name, transaction_date, delivery_date, status, total_qty, grand_total, currency
             FROM `tabSales Order` WHERE docstatus = 1"""
    if customer:
        sql += " AND customer = %s"; params.append(customer)
    if search_text:
        sql += " AND (name LIKE %s OR customer_name LIKE %s)"; params.extend([f"%{search_text}%", f"%{search_text}%"])
    if month:
        try:
            if "-" in month and len(month.split("-")[-1]) == 2:
                dt = datetime.strptime(month, "%b-%y")
            else:
                dt = datetime.strptime(month, "%Y-%m")
            sql += " AND YEAR(transaction_date)=%s AND MONTH(transaction_date)=%s"; params.extend([dt.year, dt.month])
        except Exception:
            pass
    sql += " ORDER BY transaction_date DESC LIMIT %s"; params.append(int(limit))
    rows = frappe.db.sql(sql, tuple(params), as_dict=True) or []
    result = []
    for r in rows:
        result.append({
            "name": r.get("name"),
            "customer": r.get("customer"),
            "customer_name": r.get("customer_name"),
            "transaction_date": r.get("transaction_date"),
            "month": _month_str_from_date(r.get("transaction_date")),
            "delivery_date": r.get("delivery_date"),
            "status": r.get("status"),
            "total_qty": r.get("total_qty"),
            "grand_total": r.get("grand_total"),
            "currency": r.get("currency")
        })
    return result

@frappe.whitelist()
def get_items_for_sales_orders(so_list=None):
    if not so_list: return []
    if isinstance(so_list, str):
        try: so_list = json.loads(so_list)
        except Exception: so_list = [s.strip() for s in so_list.split(',') if s.strip()]
    if not so_list: return []
    placeholders = ','.join(['%s']*len(so_list))
    sql = f"""SELECT soi.name, soi.parent as so_name, soi.item_code, soi.item_name, soi.qty as order_qty, soi.rate, soi.bom_no, soi.warehouse
        FROM `tabSales Order Item` soi
        WHERE soi.parent IN ({placeholders})
        ORDER BY soi.parent, soi.idx"""
    rows = frappe.db.sql(sql, tuple(so_list), as_dict=True) or []
    result = []
    for line in rows:
        # reuse simple computations from previous API; keep lightweight here
        bin_row = frappe.db.sql("SELECT IFNULL(SUM(actual_qty),0) as actual_qty, IFNULL(SUM(stock_value),0) as stock_value FROM `tabBin` WHERE item_code=%s", (line.item_code,), as_dict=True) or [{'actual_qty':0,'stock_value':0}]
        dispatched = frappe.db.sql("SELECT IFNULL(SUM(dni.qty),0) as qty, IFNULL(SUM(dni.amount),0) as amount FROM `tabDelivery Note Item` dni JOIN `tabDelivery Note` dn ON dn.name = dni.parent WHERE dni.against_sales_order=%s AND dni.item_code=%s AND dn.docstatus=1", (line.parent,line.item_code), as_dict=True) or [{'qty':0,'amount':0}]
        produced = frappe.db.sql("SELECT IFNULL(SUM(produced_qty),0) as produced_qty FROM `tabWork Order` WHERE sales_order=%s AND production_item=%s", (line.parent, line.item_code), as_dict=True) or [{'produced_qty':0}]
        produced_qty = produced[0].get('produced_qty',0)
        result.append({
            'so_name': line.parent,
            'item_code': line.item_code,
            'item_name': line.item_name,
            'order_qty': line.order_qty,
            'rate': line.rate,
            'bom_no': safe(line.bom_no),
            'warehouse': safe(line.warehouse),
            'available_stock_nos': bin_row[0].get('actual_qty',0),
            'available_stock_amt': bin_row[0].get('stock_value',0),
            'dispatched_qty_nos': dispatched[0].get('qty',0),
            'dispatched_amt': dispatched[0].get('amount',0),
            'produced_stock_nos': produced_qty,
            'balance_to_produce_qty': (line.order_qty or 0) - produced_qty,
            'balance_to_deliver_qty': (line.order_qty or 0) - (dispatched[0].get('qty',0) or 0)
        })
    return result

@frappe.whitelist()
def get_boms_for_items(items=None):
    if not items: return []
    if isinstance(items, str):
        try: items = json.loads(items)
        except Exception: return []
    result = []
    added = set()
    for it in items:
        item_code = it.get('item_code')
        req = float(it.get('required_for_selected_qty') or 0)
        forced_bom = it.get('bom_no')
        if forced_bom:
            boms = frappe.get_all('BOM', filters={'name': forced_bom}, fields=['name as bom_no','item','quantity as bom_qty'])
        else:
            boms = frappe.get_all('BOM', filters={'item': item_code}, fields=['name as bom_no','item','quantity as bom_qty'])
        for b in boms:
            if b['bom_no'] in added: continue
            added.add(b['bom_no'])
            items_comp = frappe.get_all('BOM Item', filters={'parent': b['bom_no']}, fields=['item_code as rm_item_code','item_name','stock_qty as qty'], order_by='idx')
            result.append({'item_code': item_code, 'bom_no': b['bom_no'], 'bom_qty': b.get('bom_qty') or 0, 'bom_items': items_comp, 'required_for_selected_qty': req})
    return result

@frappe.whitelist()
def get_raw_materials_for_boms(boms=None):
    if not boms: return []
    if isinstance(boms, str):
        try: boms = json.loads(boms)
        except: boms = []
    totals = {}
    for b in boms:
        bom_no = b.get('bom_no')
        req = float(b.get('required_for_selected_qty') or 0)
        if not bom_no: continue
        bom = frappe.db.sql('SELECT quantity as bom_qty FROM `tabBOM` WHERE name=%s', (bom_no,), as_dict=True) or [{'bom_qty':1}]
        bom_qty = bom[0].get('bom_qty') or 1.0
        comps = frappe.db.sql('SELECT item_code, item_name, stock_qty as qty FROM `tabBOM Item` WHERE parent=%s', (bom_no,), as_dict=True) or []
        for c in comps:
            rm = c.get('item_code')
            req_comp = (req / (bom_qty or 1.0)) * (c.get('qty') or 0.0)
            if rm not in totals: totals[rm] = {'rm_item_code': rm, 'rm_item_name': c.get('item_name') or '', 'total_required_qty': 0.0}
            totals[rm]['total_required_qty'] += req_comp
    out = []
    for rm, v in totals.items():
        bin_row = frappe.db.sql('SELECT IFNULL(SUM(actual_qty),0) as actual_qty FROM `tabBin` WHERE item_code=%s', (rm,), as_dict=True) or [{'actual_qty':0}]
        consumed = frappe.db.sql("SELECT IFNULL(SUM(sei.qty),0) as consumed_qty FROM `tabStock Entry Detail` sei JOIN `tabStock Entry` se ON se.name=sei.parent WHERE sei.item_code=%s AND se.docstatus=1 AND se.purpose IN ('Manufacture','Material Consumption for Manufacture')", (rm,), as_dict=True) or [{'consumed_qty':0}]
        out.append({'rm_item_code': rm, 'rm_item_name': v['rm_item_name'], 'total_required_qty': round(v['total_required_qty'],6), 'available_qty': bin_row[0].get('actual_qty',0), 'consumed_qty': consumed[0].get('consumed_qty',0)})
    return out

@frappe.whitelist()
def get_work_orders_for_sales_orders(so_list=None):
    if not so_list: return []
    if isinstance(so_list, str):
        try: so_list = json.loads(so_list)
        except: so_list = [s.strip() for s in so_list.split(',') if s.strip()]
    if not so_list: return []
    placeholders = ','.join(['%s']*len(so_list))
    sql = f"SELECT name as wo_name, production_item, qty as wo_qty, IFNULL(produced_qty,0) as produced_qty, sales_order FROM `tabWork Order` WHERE sales_order IN ({placeholders}) AND docstatus=1 ORDER BY modified DESC"
    return frappe.db.sql(sql, tuple(so_list), as_dict=True) or []

@frappe.whitelist()
def get_job_cards_for_work_orders(wo_list=None):
    if not wo_list: return []
    if isinstance(wo_list, str):
        try: wo_list = json.loads(wo_list)
        except: wo_list = [s.strip() for s in wo_list.split(',') if s.strip()]
    if not wo_list: return []
    placeholders = ','.join(['%s']*len(wo_list))
    jcs = frappe.db.sql(f"SELECT name as job_card, status as job_card_status, operation, workstation, work_order FROM `tabJob Card` WHERE work_order IN ({placeholders})", tuple(wo_list), as_dict=True) or []
    result = []
    for jc in jcs:
        jc_items = frappe.db.sql('SELECT item_code, item_name, required_qty as qty FROM `tabJob Card Item` WHERE parent=%s', (jc.job_card,), as_dict=True) or []
        if jc_items:
            for ji in jc_items:
                consumed = frappe.db.sql("SELECT IFNULL(SUM(sei.qty),0) as consumed_qty FROM `tabStock Entry Detail` sei JOIN `tabStock Entry` se ON se.name=sei.parent WHERE se.job_card IN (SELECT name FROM `tabJob Card` WHERE work_order=%s) AND sei.item_code=%s AND se.docstatus=1 AND se.purpose IN ('Manufacture','Material Consumption for Manufacture')", (jc.work_order, ji.get('item_code')), as_dict=True) or [{'consumed_qty':0}]
                bin_row = frappe.db.sql('SELECT IFNULL(SUM(actual_qty),0) as actual_qty FROM `tabBin` WHERE item_code=%s', (ji.get('item_code'),), as_dict=True) or [{'actual_qty':0}]
                result.append({'job_card': jc.name, 'job_card_status': jc.job_card_status, 'operation': jc.operation, 'workstation': jc.workstation, 'rm_item_code': ji.get('item_code'), 'rm_item_name': ji.get('item_name'), 'required_qty': ji.get('qty'), 'available_qty': bin_row[0].get('actual_qty',0), 'consumed_qty': consumed[0].get('consumed_qty',0)})
        else:
            result.append({'job_card': jc.name, 'job_card_status': jc.job_card_status, 'operation': jc.operation, 'workstation': jc.workstation, 'rm_item_code': '', 'rm_item_name': '', 'required_qty': 0, 'available_qty': 0, 'consumed_qty': 0})
    return result

@frappe.whitelist()
def save_schedule_qty(data=None):
    if not data: return {'saved':0}
    if isinstance(data, str):
        try: data = json.loads(data)
        except: data = []
    # simple persistence into a single-doctype 'MSS Monthly Schedule' could be implemented; for now store as JSON in a single Settings doctype
    frappe.db.set_value('Global Defaults', None, 'mss_last_saved_schedule', json.dumps(data))
    return {'saved': len(data)}

@frappe.whitelist()
def create_work_orders(items=None):
    if not items: return {'created': []}
    if isinstance(items, str):
        try: items = json.loads(items)
        except: items = []
    created = []
    for it in items:
        try:
            wo = frappe.get_doc({'doctype':'Work Order','production_item': it.get('item_code'), 'qty': it.get('qty') or 0, 'status':'Draft', 'planned_start_date': frappe.utils.nowdate(), 'company': frappe.defaults.get_global_default('company')})
            wo.insert()
            created.append(wo.name)
        except Exception as e:
            frappe.log_error(f'WO create failed: {e}', 'create_work_orders')
    return {'created': created}