# aims_customization/api/mss_monthly_schedule.py
from __future__ import annotations
import json
from datetime import datetime
import frappe
from frappe.utils import nowdate

# -------------------- Helpers --------------------
def safe(val):
    return val if val not in (None, "") else ""

def _month_str_from_date(dt):
    if not dt:
        return ""
    if isinstance(dt, str):
        try:
            dt = datetime.strptime(dt, "%Y-%m-%d")
        except Exception:
            return ""
    return dt.strftime("%b-%y")

def _get_bin_totals(item_code: str) -> dict:
    row = frappe.db.sql("""
        SELECT IFNULL(SUM(actual_qty),0) AS actual_qty,
               IFNULL(SUM(stock_value),0) AS stock_value
        FROM `tabBin` WHERE item_code=%s
    """, (item_code,), as_dict=True)
    return row[0] if row else {"actual_qty": 0, "stock_value": 0}

def _get_dispatched_totals(sales_order: str, item_code: str) -> dict:
    row = frappe.db.sql("""
        SELECT IFNULL(SUM(dni.qty),0) AS qty,
               IFNULL(SUM(dni.amount),0) AS amount
        FROM `tabDelivery Note Item` dni
        JOIN `tabDelivery Note` dn ON dn.name = dni.parent
        WHERE dni.against_sales_order=%s AND dni.item_code=%s AND dn.docstatus=1
    """, (sales_order, item_code), as_dict=True)
    return row[0] if row else {"qty": 0, "amount": 0}

def _get_production_totals(sales_order: str, item_code: str) -> dict:
    row = frappe.db.sql("""
        SELECT IFNULL(SUM(produced_qty),0) AS produced_qty,
               IFNULL(SUM(material_transferred_for_manufacturing),0) AS material_transferred_for_manufacturing
        FROM `tabWork Order`
        WHERE sales_order=%s AND production_item=%s
    """, (sales_order, item_code), as_dict=True)
    return row[0] if row else {"produced_qty": 0, "material_transferred_for_manufacturing": 0}

def _get_jobcard_consumed_for_wo(wo_name: str, item_code: str) -> float:
    row = frappe.db.sql("""
        SELECT IFNULL(SUM(sei.qty),0) AS consumed_qty
        FROM `tabStock Entry Detail` sei
        JOIN `tabStock Entry` se ON se.name = sei.parent
        WHERE se.job_card IN (SELECT name FROM `tabJob Card` WHERE work_order=%s)
          AND sei.item_code=%s AND se.docstatus=1
          AND se.purpose IN ('Manufacture','Material Consumption for Manufacture')
    """, (wo_name, item_code), as_dict=True)
    return row[0].get("consumed_qty", 0) if row else 0

def _get_reserved_qty(item_code: str) -> float:
    row = frappe.db.sql("""
        SELECT IFNULL(SUM(actual_qty),0) AS reserved
        FROM `tabMaterial Request Item`
        WHERE item_code=%s
    """, (item_code,), as_dict=True)
    return row[0].get("reserved", 0) if row else 0

def _get_incoming_qty(item_code: str) -> float:
    row = frappe.db.sql("""
        SELECT IFNULL(SUM(pii.qty - IFNULL(pii.received_qty,0)),0) AS incoming
        FROM `tabPurchase Order Item` pii
        JOIN `tabPurchase Order` po ON po.name=pii.parent
        WHERE pii.item_code=%s AND po.docstatus=1 AND po.status NOT IN ('Completed','Closed')
    """, (item_code,), as_dict=True)
    return row[0].get("incoming", 0) if row else 0

# -------------------- Level 1: Customers & Blanket Orders --------------------
@frappe.whitelist()
def get_customers(search_text: str = None, limit: int = 20):
    sql = "SELECT name, customer_name FROM `tabCustomer` WHERE disabled=0"
    params = []

    if search_text:
        sql += " AND (name LIKE %s OR customer_name LIKE %s)"
        params.extend([f"%{search_text}%", f"%{search_text}%"])

    sql += " ORDER BY customer_name ASC LIMIT %s"
    params.append(limit)

    rows = frappe.db.sql(sql, tuple(params), as_dict=True) or []
    return [{"name": r["name"], "customer_name": r["customer_name"]} for r in rows]

@frappe.whitelist()
def get_blanket_orders(search_text: str = None, customer: str = None, month: str = None, year: str = None,  limit: int = 200):
    sql = """
        SELECT name, blanket_order_type, customer, customer_name, supplier, supplier_name,
               order_no, order_date, from_date, to_date, company, tc_name
        FROM `tabBlanket Order`
        WHERE docstatus = 1
    """
    params = []

    if customer:
        sql += " AND customer = %s"
        params.append(customer)

    if search_text:
        sql += " AND (name LIKE %s OR customer_name LIKE %s OR order_no LIKE %s)"
        params.extend([f"%{search_text}%", f"%{search_text}%", f"%{search_text}%"])

    if month:
        try:
            dt = datetime.strptime(month, "%b-%y") if "-" in month and len(month.split("-")[-1]) == 2 else datetime.strptime(month, "%Y-%m")
            sql += " AND YEAR(order_date)=%s AND MONTH(order_date)=%s"
            params.extend([dt.year, dt.month])
        except Exception:
            pass

    sql += " ORDER BY order_date DESC LIMIT %s"
    params.append(limit)

    rows = frappe.db.sql(sql, tuple(params), as_dict=True) or []
    return [
        {
            "name": r["name"],
            "blanket_order_type": r["blanket_order_type"],
            "customer": r["customer"],
            "customer_name": r["customer_name"],
            "supplier": r["supplier"],
            "supplier_name": r["supplier_name"],
            "order_no": r["order_no"],
            "order_date": r["order_date"],
            "month": _month_str_from_date(r["order_date"]),
            "from_date": r["from_date"],
            "to_date": r["to_date"],
            "company": r["company"],
            "tc_name": r["tc_name"]
        } for r in rows
    ]

# -------------------- Level 2: Items for Blanket Orders --------------------
@frappe.whitelist()
def get_items_for_blanket_orders(bo_list: str | list = None):
    if not bo_list:
        return []

    if isinstance(bo_list, str):
        try:
            bo_list = json.loads(bo_list)
        except Exception:
            bo_list = [s.strip() for s in bo_list.split(",") if s.strip()]

    if not bo_list:
        return []

    placeholders = ",".join(["%s"] * len(bo_list))
    sql = f"""
        SELECT boi.name, boi.parent AS bo_name, boi.item_code, boi.item_name, boi.qty AS order_qty, boi.rate
        FROM `tabBlanket Order Item` boi
        WHERE boi.parent IN ({placeholders})
        ORDER BY boi.parent, boi.idx
    """
    rows = frappe.db.sql(sql, tuple(bo_list), as_dict=True) or []
    result = []

    for line in rows:
        bin_tot = _get_bin_totals(line["item_code"])
        dispatched = _get_dispatched_totals(line["bo_name"], line["item_code"])
        production = _get_production_totals(line["bo_name"], line["item_code"])

        produced_qty = production.get("produced_qty", 0)
        produced_amt = produced_qty * (line.get("rate") or 0)
        material_transferred = production.get("material_transferred_for_manufacturing", 0)
        wip_qty = max(material_transferred - produced_qty, 0)
        wip_amt = wip_qty * (line.get("rate") or 0)
        total_stock_qty = (bin_tot.get("actual_qty", 0) or 0) + wip_qty
        total_stock_amt = (bin_tot.get("stock_value", 0) or 0) + wip_amt

        balance_to_produce_qty = (line.get("order_qty") or 0) - produced_qty
        balance_to_deliver_qty = (line.get("order_qty") or 0) - (dispatched.get("qty") or 0)

        item_attrs = frappe.db.get_value(
            "Item", line["item_code"],
            ["cavity", "pcs_wt", "runner_wt", "shot_wt", "weight_per_unit"], as_dict=True
        ) or {}

        result.append({
            "bo_name": line["bo_name"],
            "item_code": line["item_code"],
            "item_name": line["item_name"],
            "order_qty": line["order_qty"],
            "rate": line["rate"],
            "bom_no": safe(line.get("bom_no")),
            "warehouse": safe(line.get("warehouse")),

            # Item attributes
            "cavity": safe(item_attrs.get("cavity")),
            "pcs_wt": safe(item_attrs.get("pcs_wt")),
            "runner_wt": safe(item_attrs.get("runner_wt")),
            "shot_wt": safe(item_attrs.get("shot_wt")),
            "weight_per_unit": safe(item_attrs.get("weight_per_unit")),

            # Stock & Dispatch
            "available_stock_nos": bin_tot.get("actual_qty", 0),
            "available_stock_amt": bin_tot.get("stock_value", 0),
            "dispatched_qty_nos": dispatched.get("qty", 0),
            "dispatched_amt": dispatched.get("amount", 0),

            # Production & WIP
            "produced_stock_nos": produced_qty,
            "produced_stock_amt": produced_amt,
            "wip_stock_nos": wip_qty,
            "wip_stock_amt": wip_amt,

            "total_stock_nos": total_stock_qty,
            "total_stock_amt": total_stock_amt,
            "total_plus_produced_nos": total_stock_qty + produced_qty,
            "total_plus_produced_amt": total_stock_amt + produced_amt,

            "balance_to_produce_qty": balance_to_produce_qty,
            "balance_to_produce_amt": balance_to_produce_qty * (line.get("rate") or 0),
            "balance_to_deliver_qty": balance_to_deliver_qty,
            "balance_to_deliver_amt": balance_to_deliver_qty * (line.get("rate") or 0),

            # Reserved / Incoming
            "reserved_qty": _get_reserved_qty(line["item_code"]),
            "incoming_qty": _get_incoming_qty(line["item_code"]),
        })

    return result

@frappe.whitelist()
def create_sales_order(blanket_order: str, items: str | list):
    if isinstance(items, str):
        items = json.loads(items)

    if not items:
        frappe.throw("No items selected.")

    bo = frappe.get_doc("Blanket Order", blanket_order)
    so = frappe.new_doc("Sales Order")

    so.customer = bo.customer
    so.delivery_date = nowdate()
    so.company = bo.company
    so.currency = bo.currency
    so.blanket_order = blanket_order

    for it in items:
        so.append("items", {
            "item_code": it.get("item_code"),
            "item_name": it.get("item_name"),
            "qty": it.get("order_qty"),
            "rate": it.get("rate"),
            "delivery_date": nowdate(),
            "bom_no": it.get("bom_no"),
            "warehouse": it.get("warehouse"),
            "blanket_order": blanket_order,
            "blanket_order_rate": it.get("rate"),
        })

    so.flags.ignore_mandatory = True
    so.insert(ignore_permissions=True)

    return {
        "status": "success",
        "message": "Sales Order Created",
        "sales_order": so.name
    }

# -------------------- Level 3: Sales Orders --------------------
@frappe.whitelist()
def get_sales_orders(search_text: str = None, month: str = None, customer: str = None, limit: int = 200):
    sql = """
        SELECT name, customer, customer_name, transaction_date, delivery_date, status
        FROM `tabSales Order`
        WHERE docstatus = 1
    """
    params = []

    if customer:
        sql += " AND customer = %s"
        params.append(customer)

    if search_text:
        sql += " AND (name LIKE %s OR customer_name LIKE %s)"
        params.extend([f"%{search_text}%", f"%{search_text}%"])

    if month:
        try:
            dt = datetime.strptime(month, "%b-%y") if "-" in month and len(month.split("-")[-1]) == 2 else datetime.strptime(month, "%Y-%m")
            sql += " AND YEAR(transaction_date)=%s AND MONTH(transaction_date)=%s"
            params.extend([dt.year, dt.month])
        except Exception:
            pass

    sql += " ORDER BY transaction_date DESC LIMIT %s"
    params.append(limit)

    rows = frappe.db.sql(sql, tuple(params), as_dict=True) or []
    return [
        {
            "name": r["name"],
            "customer": r["customer"],
            "customer_name": r["customer_name"],
            "transaction_date": r["transaction_date"],
            "month": _month_str_from_date(r["transaction_date"]),
            "delivery_date": r["delivery_date"],
            "status": r["status"]
        } for r in rows
    ]

# -------------------- Level 4: BOMs for selected items --------------------
@frappe.whitelist()
def get_boms_for_items(items: str | list = None):
    if not items:
        return []

    if isinstance(items, str):
        try:
            items = json.loads(items)
        except Exception as e:
            frappe.log_error(f"Failed to parse items JSON: {e}", "get_boms_for_items")
            return []

    result = []

    for it in items:
        item_code = it.get("item_code")
        required_qty = float(it.get("required_for_selected_qty") or 0)
        forced_bom = it.get("bom_no")

        boms = (frappe.get_all(
            "BOM",
            filters={"name": forced_bom} if forced_bom else {"item": item_code, "is_active": 1},
            fields=["name as bom_no", "item as item", "quantity as bom_qty"],
            limit_page_length=1 if forced_bom else None
        ) or [])

        for b in boms:
            bom_items = frappe.get_all(
                "BOM Item",
                filters={"parent": b["bom_no"]},
                fields=["item_code as rm_item_code", "item_name", "stock_qty as qty_per_bom"],
                order_by="idx"
            )
            result.append({
                "item_code": item_code,
                "bom_no": b.get("bom_no"),
                "bom_qty": b.get("bom_qty") or 0,
                "bom_items": bom_items,
                "required_for_selected_qty": required_qty
            })

    return result

# -------------------- Level 5: Raw materials for selected BOMs --------------------
@frappe.whitelist()
def get_raw_materials_for_boms(boms: str | list = None):
    if not boms:
        return []

    if isinstance(boms, str):
        try:
            boms = json.loads(boms)
        except Exception:
            return []

    rm_totals = {}

    for b in boms:
        bom_no = b.get("bom_no")
        req_qty = float(b.get("required_for_selected_qty") or 0)
        if not bom_no:
            continue

        bom = frappe.db.get_value("BOM", bom_no, "quantity") or 1.0
        components = frappe.db.sql("""
            SELECT item_code, item_name, stock_qty AS qty
            FROM `tabBOM Item` WHERE parent=%s
        """, (bom_no,), as_dict=True) or []

        for comp in components:
            comp_required = (req_qty / bom) * (comp.get("qty") or 0.0)
            rm = comp["item_code"]
            if rm not in rm_totals:
                rm_totals[rm] = {"rm_item_code": rm, "rm_item_name": comp.get("item_name") or "", "total_required_qty": 0.0}
            rm_totals[rm]["total_required_qty"] += comp_required

    result = []
    for rm, v in rm_totals.items():
        bin_tot = _get_bin_totals(rm)
        consumed_row = frappe.db.sql("""
            SELECT IFNULL(SUM(sei.qty),0) AS consumed_qty
            FROM `tabStock Entry Detail` sei
            JOIN `tabStock Entry` se ON se.name=sei.parent
            WHERE sei.item_code=%s AND se.docstatus=1
              AND se.purpose IN ('Manufacture','Material Consumption for Manufacture')
        """, (rm,), as_dict=True)
        consumed = consumed_row[0].get("consumed_qty", 0) if consumed_row else 0

        result.append({
            "rm_item_code": v["rm_item_code"],
            "rm_item_name": v["rm_item_name"],
            "total_required_qty": round(v["total_required_qty"], 6),
            "available_qty": bin_tot.get("actual_qty", 0),
            "consumed_qty": consumed
        })

    return result

# -------------------- Level 6: Work Orders for Blanket Orders --------------------
@frappe.whitelist()
def get_work_orders_for_blanket_orders(bo_list: str | list = None):
    if not bo_list:
        return []

    if isinstance(bo_list, str):
        try:
            bo_list = json.loads(bo_list)
        except Exception:
            bo_list = [s.strip() for s in bo_list.split(",") if s.strip()]

    if not bo_list:
        return []

    placeholders = ",".join(["%s"] * len(bo_list))
    sql = f"""
        SELECT name AS wo_name, production_item, qty AS wo_qty, IFNULL(produced_qty,0) AS produced_qty, sales_order
        FROM `tabWork Order`
        WHERE sales_order IN ({placeholders}) AND docstatus=1
        ORDER BY modified DESC
    """
    return frappe.db.sql(sql, tuple(bo_list), as_dict=True) or []

# -------------------- Level 7: Job Cards for Work Orders --------------------
@frappe.whitelist()
def get_job_cards_for_work_orders(wo_list: str | list = None):
    if not wo_list:
        return []

    if isinstance(wo_list, str):
        try:
            wo_list = json.loads(wo_list)
        except Exception:
            wo_list = [s.strip() for s in wo_list.split(",") if s.strip()]

    if not wo_list:
        return []

    placeholders = ",".join(["%s"] * len(wo_list))
    jcs = frappe.db.sql(f"""
        SELECT name AS job_card, status AS job_card_status, operation, workstation, work_order
        FROM `tabJob Card` WHERE work_order IN ({placeholders})
    """, tuple(wo_list), as_dict=True) or []

    result = []
    for jc in jcs:
        jc_items = frappe.db.sql("""
            SELECT item_code, item_name, required_qty AS qty
            FROM `tabJob Card Item` WHERE parent=%s
        """, (jc["job_card"],), as_dict=True) or []

        if jc_items:
            for ji in jc_items:
                consumed = _get_jobcard_consumed_for_wo(jc["work_order"], ji["item_code"])
                bin_tot = _get_bin_totals(ji["item_code"])
                result.append({
                    "job_card": jc["job_card"],
                    "job_card_status": jc["job_card_status"],
                    "operation": jc["operation"],
                    "workstation": jc["workstation"],
                    "rm_item_code": ji["item_code"],
                    "rm_item_name": ji["item_name"],
                    "required_qty": ji["qty"],
                    "available_qty": bin_tot.get("actual_qty", 0),
                    "consumed_qty": consumed
                })
        else:
            result.append({
                "job_card": jc["job_card"],
                "job_card_status": jc["job_card_status"],
                "operation": jc["operation"],
                "workstation": jc["workstation"],
                "rm_item_code": "",
                "rm_item_name": "",
                "required_qty": 0,
                "available_qty": 0,
                "consumed_qty": 0
            })

    return result

# ---------------- LEVEL 8: Production / QC / Updates ----------------

@frappe.whitelist()
def attach_qc_job_card(job_card, qc_item_code):
    """
    Attach a QC item to a Job Card.
    """
    if not job_card or not qc_item_code:
        frappe.throw("Job Card and QC Item are required.")

    # Check if QC already exists
    exists = frappe.db.exists("Job Card QC", {"parent": job_card, "qc_item_code": qc_item_code})
    if not exists:
        doc = frappe.new_doc("Job Card QC")
        doc.parent = job_card
        doc.parentfield = "qc_checks"
        doc.parenttype = "Job Card"
        doc.qc_item_code = qc_item_code
        doc.status = "Pending"
        doc.insert(ignore_permissions=True)
    return {"status": "success", "message": f"QC item {qc_item_code} attached to Job Card {job_card}"}


@frappe.whitelist()
def add_scrap_job_card(job_card, scrap_qty):
    """
    Record scrap quantity for a Job Card.
    """
    if not job_card or scrap_qty is None:
        frappe.throw("Job Card and Scrap Quantity are required.")
    scrap_qty = float(scrap_qty)

    # Create Stock Entry for Scrap
    se = frappe.new_doc("Stock Entry")
    se.stock_entry_type = "Material Issue"
    se.purpose = "Scrap"
    se.to_warehouse = None
    se.append("items", {
        "item_code": frappe.db.get_value("Job Card Item", {"parent": job_card}, "item_code"),
        "qty": scrap_qty,
        "s_warehouse": frappe.db.get_value("Job Card Item", {"parent": job_card}, "warehouse"),
    })
    se.flags.ignore_mandatory = True
    se.insert(ignore_permissions=True)
    se.submit()
    return {"status": "success", "message": f"Scrap of {scrap_qty} recorded for Job Card {job_card}"}


@frappe.whitelist()
def create_work_orders(bo_list):
    """
    Create Work Orders for selected Blanket Orders.
    """
    if isinstance(bo_list, str):
        bo_list = json.loads(bo_list)

    created_wos = []

    for bo_name in bo_list:
        items = frappe.get_all("Blanket Order Item", filters={"parent": bo_name}, fields=["item_code", "qty", "warehouse", "bom_no"])
        bo_doc = frappe.get_doc("Blanket Order", bo_name)
        for item in items:
            wo = frappe.new_doc("Work Order")
            wo.production_item = item.item_code
            wo.qty = item.qty
            wo.sales_order = bo_name
            wo.company = bo_doc.company
            wo.bom_no = item.bom_no
            wo.fg_warehouse = item.warehouse
            wo.flags.ignore_mandatory = True
            wo.insert(ignore_permissions=True)
            created_wos.append(wo.name)

    return {"status": "success", "created_work_orders": created_wos}


@frappe.whitelist()
def update_job_card_status(job_card, status):
    """
    Update status of a Job Card.
    """
    if not job_card or not status:
        frappe.throw("Job Card and Status are required.")
    frappe.db.set_value("Job Card", job_card, "status", status)
    frappe.db.commit()
    return {"status": "success", "job_card": job_card, "new_status": status}


@frappe.whitelist()
def get_production_status(bo_list):
    """
    Aggregate production status for Blanket Orders.
    """
    if isinstance(bo_list, str):
        bo_list = json.loads(bo_list)
    if not bo_list:
        return []

    placeholders = ",".join(["%s"] * len(bo_list))
    wo_rows = frappe.db.sql(f"""
        SELECT sales_order AS bo_name,
               production_item,
               SUM(qty) AS total_qty,
               SUM(IFNULL(produced_qty,0)) AS produced_qty
        FROM `tabWork Order`
        WHERE sales_order IN ({placeholders}) AND docstatus=1
        GROUP BY sales_order, production_item
    """, tuple(bo_list), as_dict=True)

    result = []
    for wo in wo_rows:
        balance_qty = (wo.total_qty or 0) - (wo.produced_qty or 0)
        result.append({
            "bo_name": wo.bo_name,
            "item_code": wo.production_item,
            "total_qty": wo.total_qty,
            "produced_qty": wo.produced_qty,
            "balance_qty": balance_qty,
            "progress_percent": round((wo.produced_qty or 0) / (wo.total_qty or 1) * 100, 2)
        })
    return result
