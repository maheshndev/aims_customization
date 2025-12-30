# aims_customization/api/mss_monthly_schedule.py
from __future__ import annotations
import json
from datetime import datetime, timedelta, time
import calendar
import frappe
from frappe.utils import nowdate, get_datetime, flt, get_last_day, get_first_day, cint, getdate, add_days
from frappe import _
from frappe.model.document import Document

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
    return dt.strftime("%B-%Y")

def get_date_range(month=None, year=None):
    
    m = None
    y = None

    if year:
        try:
            y = int(year)
        except ValueError:
            return None

    if month:
        s = str(month).strip()

        for sep in ("-", "/"):
            if sep in s:
                p1, p2 = s.split(sep, 1)
                if p1.isdigit() and len(p1) == 4:  
                    y = int(p1)
                    s = p2
                elif p2.isdigit() and len(p2) == 4:  
                    y = int(p2)
                    s = p1
                break

        if s.isdigit():
            m = int(s)
            if not (1 <= m <= 12):
                m = None
        else:
            try:
                m = datetime.strptime(s[:3].title(), "%b").month
            except Exception:
                try:
                    m = list(calendar.month_name).index(s.title())
                except Exception:
                    m = None             
    if y and m:  
        start_date = f"{y}-{m:02d}-01"
        end_date = get_last_day(start_date)
        return {"type": "month_year", "start": start_date, "end": end_date}
    elif y and not m:  
        start_date = f"{y}-01-01"
        end_date = f"{y}-12-31"
        return {"type": "year", "start": start_date, "end": end_date}
    elif m and not y: 
        return {"type": "month_only", "month": m}

    return None

def _get_bin_totals(item_code: str) -> dict:
    row = frappe.db.sql("""
        SELECT IFNULL(SUM(actual_qty),0) AS actual_qty,
               IFNULL(SUM(stock_value),0) AS stock_value
        FROM `tabBin` WHERE item_code=%s
    """, (item_code,), as_dict=True)
    return row[0] if row else {"actual_qty": 0, "stock_value": 0}

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

def _get_so_consumed_qty(bo_name, item_code):
    """Returns total qty used in Sales Orders linked to this Blanket Order for this item."""
    data = frappe.db.sql("""
        SELECT SUM(soi.qty) AS qty
        FROM `tabSales Order Item` soi
        JOIN `tabSales Order` so ON so.name = soi.parent
        WHERE soi.blanket_order = %s
          AND soi.item_code = %s
          AND so.docstatus < 2
    """, (bo_name, item_code), as_dict=True)

    return data[0].qty or 0

##### -------------------- Level 0: Customers in Filters Section -------------------- #####
@frappe.whitelist()
def get_customers(search_text: str = None, customer_id: str = None, limit: int = 20):
    
    sql = "SELECT name, customer_name FROM `tabCustomer` WHERE disabled=0"
    params = []

    if customer_id:
        sql += " AND name = %s"
        params.append(customer_id)
    elif search_text:
        sql += " AND (name LIKE %s OR customer_name LIKE %s)"
        params.extend([f"%{search_text}%", f"%{search_text}%"])
        sql += " ORDER BY customer_name ASC LIMIT %s"
        params.append(limit)
    else:
        sql += " ORDER BY customer_name ASC LIMIT %s"
        params.append(limit)

    rows = frappe.db.sql(sql, tuple(params), as_dict=True) or []
    
    return [{"name": r["name"], "customer_name": r["customer_name"]} for r in rows]

##### -------------------- Level 1: Blanket Orders Section -------------------- #####
@frappe.whitelist()
def get_blanket_orders(search_text=None, customer=None, month=None, year=None, limit=500):
    
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

    date_filter = get_date_range(month, year)

    if date_filter:
        if date_filter["type"] in ("month_year", "year"):
            sql += " AND order_date BETWEEN %s AND %s"
            params.extend([date_filter["start"], date_filter["end"]])
        elif date_filter["type"] == "month_only":
            sql += " AND MONTH(order_date)=%s" 
            params.append(month) 

    sql += " ORDER BY order_date DESC LIMIT %s"
    params.append(limit)

    rows = frappe.db.sql(sql, tuple(params), as_dict=True) or []
    
    if not rows:
        return []

    bo_names = [r["name"] for r in rows]
    placeholders = ", ".join(["%s"] * len(bo_names))
    total_qty_map = {}
    total_qty_rows = frappe.db.sql(f"""
        SELECT parent, SUM(qty) AS total_qty
        FROM `tabBlanket Order Item`
        WHERE parent IN ({placeholders})
        GROUP BY parent
    """, tuple(bo_names), as_dict=True) or []

    for r in total_qty_rows:
        total_qty_map[r["parent"]] = flt(r["total_qty"])

    used_qty_map = {}
    used_qty_rows = frappe.db.sql(f"""
        SELECT soi.blanket_order, SUM(soi.qty) AS used_qty
        FROM `tabSales Order Item` soi
        JOIN `tabSales Order` so ON so.name = soi.parent
        WHERE soi.blanket_order IN ({placeholders}) 
          AND so.docstatus = 1 
        GROUP BY soi.blanket_order
    """, tuple(bo_names), as_dict=True) or []

    for r in used_qty_rows:
        used_qty_map[r["blanket_order"]] = flt(r["used_qty"])
        
    result = []
    for r in rows:
        bo_name = r["name"]
        total_bo_qty = total_qty_map.get(bo_name, 0.0)
        used_qty = used_qty_map.get(bo_name, 0.0)
        remaining_qty = total_bo_qty - used_qty
        r["total_blanket_qty"] = total_bo_qty
        r["remaining_qty"] = remaining_qty
        r["month"] = _month_str_from_date(r["order_date"])
        
        result.append(r)

    return result

##### -------------------- Level 2: Items for Blanket Orders Section -------------------- #####
@frappe.whitelist()
def get_blanket_orders_with_items( search_text=None, customer=None, month=None, year=None, limit=500 ):
    sql = """
        SELECT
            bo.name AS bo_name,
            bo.customer,
            bo.customer_name,
            bo.order_date,
            boi.item_code,
            boi.item_name,
            boi.qty AS order_qty,
            boi.rate,
            boi.idx
        FROM `tabBlanket Order` bo
        JOIN `tabBlanket Order Item` boi
            ON boi.parent = bo.name
        WHERE
            bo.docstatus = 1
            AND bo.blanket_order_type = 'Selling'
    """
    
    params = []

    if customer:
        sql += " AND bo.customer = %s"
        params.append(customer)

    if search_text:
        sql += """
            AND (
                bo.name LIKE %s
                OR bo.customer_name LIKE %s
                OR boi.item_code LIKE %s
                OR boi.item_name LIKE %s
            )
        """
        params.extend([f"%{search_text}%"] * 4)

    date_filter = get_date_range(month, year)
    if date_filter:
        if date_filter["type"] in ("month_year", "year"):
            sql += " AND bo.order_date BETWEEN %s AND %s"
            params.extend([date_filter["start"], date_filter["end"]])
        elif date_filter["type"] == "month_only":
            sql += " AND MONTH(bo.order_date) = %s"
            params.append(month)

    sql += " ORDER BY bo.order_date DESC, bo.name, boi.idx LIMIT %s"
    params.append(limit)
    
    rows = frappe.db.sql(sql, tuple(params), as_dict=True) or []
    if not rows:
        return []

    bo_item_map = {}
    for r in rows:
        key = (r["bo_name"], r["item_code"])
        bo_item_map[key] = 0

    if bo_item_map:
        consumed = frappe.db.sql("""
            SELECT
                soi.blanket_order,
                soi.item_code,
                SUM(soi.qty) AS consumed_qty
            FROM `tabSales Order Item` soi
            JOIN `tabSales Order` so ON so.name = soi.parent
            WHERE so.docstatus = 1
            GROUP BY soi.blanket_order, soi.item_code
        """, as_dict=True)

        for c in consumed:
            key = (c["blanket_order"], c["item_code"])
            if key in bo_item_map:
                bo_item_map[key] = flt(c["consumed_qty"])

    result = []
    for r in rows:
        consumed_qty = bo_item_map.get((r["bo_name"], r["item_code"]), 0)
        remaining_bo_qty = flt(r["order_qty"]) - consumed_qty

        if remaining_bo_qty <= 0:
            continue

        result.append({
            "customer": r["customer"],
            "bo_name": r["bo_name"],
            "order_date": r["order_date"],
            "item_code": r["item_code"],
            "item_name": r["item_name"],
            "order_qty": flt(r["order_qty"]),
            "remaining_bo_qty": remaining_bo_qty,
            "schedule_qty": 0,
            "consumed_qty": consumed_qty,
            "rate": flt(r["rate"]),
        })

    return result

@frappe.whitelist(allow_guest=True)
def create_sales_order(items: str | list):

    if isinstance(items, str):
        items = json.loads(items)

    if not items:
        frappe.throw("No items provided.")

    orders = {}
    for it in items:
        bo_name = it.get("bo_name")
        if not bo_name:
            frappe.throw(f"Item {it.get('item_code')} is missing blanket_order")
        orders.setdefault(bo_name, []).append(it)

    created_sos = []
    skipped = []

    for bo_name, bo_items in orders.items():

        bo = frappe.get_doc("Blanket Order", bo_name)

        used_qty = frappe.db.sql("""
            SELECT SUM(soi.qty) AS qty
            FROM `tabSales Order Item` soi
            JOIN `tabSales Order` so ON so.name = soi.parent
            WHERE soi.blanket_order = %s AND so.docstatus < 2
        """, (bo_name,), as_dict=True)[0].qty or 0

        total_bo_qty = sum(row.qty for row in bo.items)
        remaining_qty = total_bo_qty - used_qty

        if remaining_qty <= 0:
            skipped.append({
                "blanket_order": bo_name,
                "reason": "Can not Create Sales Order because Fully consumed",
                "total_qty": total_bo_qty,
                "used_qty": used_qty,
                "remaining_qty": 0
            })
            continue

        so = frappe.new_doc("Sales Order")
        so.customer = bo.customer
        so.company = bo.company
        so.blanket_order = bo_name
        so.delivery_date = nowdate()
        so.currency = getattr(bo, "currency", None) or frappe.get_value("Company", bo.company, "default_currency") or "USD"
        so.status = "Draft"

        for it in bo_items:
            item_doc = frappe.get_doc("Item", it.get("item_code"))

            warehouse = (
                it.get("warehouse") or frappe.get_value("Item Default", {"parent": it.get("item_code")}, "default_warehouse") or ""
            )
            bom_no = (
                it.get("bom_no") or frappe.get_value("BOM", {"item": it.get("item_code"), "is_default": 1}, "name")
            )
            rate = it.get("rate") or item_doc.standard_rate or 0

            so.append("items", {
                "item_code": it.get("item_code"),
                "item_name": item_doc.item_name,
                "qty": it.get("schedule_qty"),
                "rate": rate,
                "delivery_date": nowdate(),
                "bom_no": bom_no,
                "warehouse": warehouse,
                "blanket_order": bo_name,
                "blanket_order_rate": rate,
            })

        so.flags.ignore_mandatory = True
        so.insert(ignore_permissions=True)
        created_sos.append(so.name)

    return {
        "status": "success",
        "message": f"{len(created_sos)} Sales Order(s) created. {len(skipped)} skipped.",
        "created_sales_orders": created_sos,
        "skipped": skipped
    }

##### -------------------- Level 3: Sales Orders Section -------------------- #####
@frappe.whitelist()
def get_sales_orders(search_text: str = None, month: str = None, year: str =None, customer: str = None, blanket_orders: list | str = None,  limit: int = 200 ):
     
    sql = """
        SELECT 
            so.name,
            so.customer,
            so.customer_name,
            so.transaction_date,
            so.delivery_date,
            so.status,
            so.total_qty
        FROM `tabSales Order` so
        WHERE 1 = 1
    """

    params = []

    if customer:
        sql += " AND so.customer = %s"
        params.append(customer)

    if search_text:
        sql += " AND (so.name LIKE %s OR so.customer_name LIKE %s)"
        like = f"%{search_text}%"
        params.extend([like, like])

    date_filter = get_date_range(month, year)

    if date_filter:
        if date_filter["type"] in ("month_year", "year"):
            sql += " AND so.transaction_date BETWEEN %s AND %s"
            params.extend([date_filter["start"], date_filter["end"]])
            
        elif date_filter["type"] == "month_only":
            sql += " AND MONTH(so.transaction_date) = %s"
            params.append(date_filter["month"])
   
    sql += " ORDER BY so.transaction_date DESC LIMIT %s"
    params.append(limit)
    orders = frappe.db.sql(sql, tuple(params), as_dict=True) or []
    result = []

    for r in orders:
        items = frappe.db.sql(
            """
            SELECT 
                soi.item_code,
                soi.item_name,
                soi.qty,
                soi.item_group,
                soi.rate,
                soi.bom_no
            FROM `tabSales Order Item` soi
            WHERE soi.parent = %s
            ORDER BY soi.idx
            """,
            (r["name"],),
            as_dict=True
        )

        result.append({
            "name": r["name"],
            "customer": r["customer"],
            "customer_name": r["customer_name"],
            "transaction_date": r["transaction_date"],
            "delivery_date": r["delivery_date"],
            "status": r["status"],
            "total_qty": r["total_qty"],
            "month": r["transaction_date"].strftime("%B-%Y"),
            "items": items,
        })

    return result

##### -------------------- Level 4: BOMs for Sales Orders Section -------------------- #####
@frappe.whitelist()
def get_boms_for_sales_orders(sales_orders: str | list = None):

    if isinstance(sales_orders, str):
        try:
            sales_orders = json.loads(sales_orders)
        except Exception:
            return []

    if not sales_orders:
        return []

    result = []
    mould_cache = {}

    sales_orders_data = frappe.get_all(
        "Sales Order",
        filters={
            "name": ["in", sales_orders],
            "docstatus": 1  
        },
        fields=["name", "customer"]
    )

    valid_so_names = {so.name for so in sales_orders_data}
    customer_map = {so.name: so.customer for so in sales_orders_data}

    if not valid_so_names:
        return []

    so_items = frappe.get_all(
        "Sales Order Item",
        filters={"parent": ["in", list(valid_so_names)]},
        fields=["parent", "item_code", "qty", "bom_no"]
    )

    for so_item in so_items:
        so_name = so_item.parent
        item_code = so_item.item_code
        required_qty = flt(so_item.qty or 0)
        forced_bom = so_item.bom_no

        bom_filters = {"name": forced_bom} if forced_bom else {
            "item": item_code,
            "is_active": 1
        }

        boms = frappe.get_all(
            "BOM",
            filters=bom_filters,
            fields=["name as bom_no", "bom_type", "quantity as bom_qty"],
            limit_page_length=1 if forced_bom else 0
        )

        if not boms:
            continue

        item_data = frappe.db.get_value(
            "Item",
            item_code,
            [
                "pcs_wt", "runner_wt", "shot_wt",
                "gross_wt", "cycle_time", "cavity"
            ],
            as_dict=True
        ) or {}

        mould_nos = frappe.get_all(
            "Mould Selection",
            filters={"parent": item_code},
            pluck="mould_no",
            order_by="idx"
        )

        moulds = []
        if mould_nos:
            missing = [m for m in mould_nos if m not in mould_cache]

            if missing:
                mould_details = frappe.get_all(
                    "Mould",
                    filters={"name": ["in", list(set(missing))]},
                    fields=["name as mould_no", "mould_name", "cavity_count"]
                )

                for m in mould_details:
                    mould_cache[m.mould_no] = {
                        "mould_no": m.mould_no,
                        "mould_name": m.mould_name or "",
                        "cavity_count": int(flt(m.cavity_count or 0))
                    }

            moulds = [mould_cache[m] for m in mould_nos if m in mould_cache]

        for bom in boms:
            bom_no = bom.bom_no

            bom_items = frappe.get_all(
                "BOM Item",
                filters={"parent": bom_no},
                fields=[
                    "item_code as rm_item_code",
                    "item_name",
                    "stock_qty as qty_per_bom"
                ],
                order_by="idx"
            )

            bom_operations = frappe.get_all(
                "BOM Operation",
                filters={"parent": bom_no},
                fields=[
                    "operation", "workstation",
                    "time_in_mins", "hour_rate",
                    "operating_cost", "batch_size",
                    "cost_per_unit", "base_cost_per_unit"
                ],
                order_by="idx"
            )

            result.append({
                "sales_order": so_name,
                "customer": customer_map.get(so_name),
                "item_code": item_code,
                "bom_no": bom_no,
                "bom_type": bom.bom_type or "",
                "bom_qty": flt(bom.bom_qty or 0),
                "cavity": int(flt(item_data.get("cavity") or 0)),
                "pcs_wt": flt(item_data.get("pcs_wt") or 0),
                "runner_wt": flt(item_data.get("runner_wt") or 0),
                "shot_wt": flt(item_data.get("shot_wt") or 0),
                "gross_wt": flt(item_data.get("gross_wt") or 0),
                "cycle_time": flt(item_data.get("cycle_time") or 0),
                "bom_items": bom_items,
                "bom_operations": bom_operations,
                "moulds": moulds,
                "required_for_selected_qty": required_qty,
            })

    return result

##### -------------------- Level 5: Raw Materials for BOMs Section -------------------- #####
@frappe.whitelist()
def get_raw_materials_for_boms(boms: list = None):
   
    if not boms:
        return []

    if isinstance(boms, str):
        try:
            boms = json.loads(boms)
        except Exception:
            return []

    rm_totals = {}
    
    for b in boms:
        if not isinstance(b, dict):
            continue 
            
        bom_no = b.get("bom_no")
        req_qty = flt(b.get("required_for_selected_qty")) 
        
        if not bom_no or req_qty <= 0:
            continue

        bom_qty = flt(frappe.db.get_value("BOM", bom_no, "quantity") or 1.0)

        components = frappe.db.sql("""
            SELECT item_code, item_name, stock_qty AS qty, uom
            FROM `tabBOM Item` 
            WHERE parent=%s
        """, (bom_no,), as_dict=True) or []

        for comp in components:
            comp_item_code = comp["item_code"]
            qty_per_bom_unit = flt(comp.get("qty"))
            comp_required = (req_qty / bom_qty) * qty_per_bom_unit

            if comp_item_code not in rm_totals:
                rm_totals[comp_item_code] = {
                    "rm_item_code": comp_item_code,
                    "rm_item_name": comp.get("item_name") or "",
                    "uom": comp.get("uom") or "",
                    "total_required_qty": 0.0,
                }
            
            rm_totals[comp_item_code]["total_required_qty"] += comp_required

    rm_item_codes = list(rm_totals.keys())
    
    item_master_data = frappe.get_all(
        "Item",
        filters={"name": ["in", rm_item_codes]},
        fields=["name", "stock_uom"],
    )
    item_data_map = {d.name: d for d in item_master_data}

    consumed_data = frappe.db.sql("""
        SELECT sei.item_code, IFNULL(SUM(sei.qty),0) AS consumed_qty
        FROM `tabStock Entry Detail` sei
        JOIN `tabStock Entry` se ON se.name=sei.parent
        WHERE sei.item_code IN %(item_codes)s AND se.docstatus=1
          AND se.purpose IN ('Manufacture', 'Material Consumption for Manufacture')
        GROUP BY sei.item_code
    """, {"item_codes": rm_item_codes}, as_dict=True)

    consumed_map = {row["item_code"]: flt(row["consumed_qty"]) for row in consumed_data}
    
    result = []
    
    for rm_code, v in rm_totals.items():
        item_master = item_data_map.get(rm_code, {})
        bin_tot = _get_bin_totals(rm_code) 
        required = round(v["total_required_qty"], 6)
        available = flt(bin_tot.get("actual_qty", 0))
        consumed = consumed_map.get(rm_code, 0)
        projected = flt(bin_tot.get("projected_qty", 0))
        balance_qty = available - required
        is_sufficient = balance_qty >= 0

        result.append({
            "rm_item_code": rm_code,
            "rm_item_name": v["rm_item_name"],
            "stock_uom": item_master.get("stock_uom") or v["uom"],
            "default_warehouse": item_master.get("default_warehouse") or "",
            "total_required_qty": required,
            "available_qty": available,
            "projected_qty": projected,
            "consumed_qty": consumed,
            "balance_qty": round(balance_qty, 6),
            "is_sufficient": is_sufficient
        })

    return result


##### ------- Capacity Planning Helpers & Work Order Creation ------- #####
##### ------------- Helpers for Capacity Planning -------------------- #####

def _to_time(val):
    if isinstance(val, time):
        return val
    if isinstance(val, timedelta):
        s = int(val.total_seconds())
        return time((s // 3600) % 24, (s % 3600) // 60, s % 60)
    return None

def combine_datetime(date, t):
    return datetime.combine(date, _to_time(t))

def pcs_per_hour(cycle_time, cavity):
    cycle = flt(cycle_time)
    cavity = max(1, cint(cavity))
    if cycle <= 0:
        frappe.throw(_("Invalid cycle time"))
    return (3600 / cycle) * cavity

def get_holidays(holiday_list):
    holidays = set()
    if holiday_list:
        for h in frappe.get_all("Holiday", filters={"parent": holiday_list}, fields=["holiday_date"]):
            holidays.add(h.holiday_date)
    return holidays

def get_shift_windows(start_date, end_date):
    windows = []
    start_date = getdate(start_date)
    end_date = getdate(end_date)

    shift_types = frappe.get_all(
        "Shift Type",
        fields=["name", "start_time", "end_time"],
        order_by="start_time"
    )

    day = start_date
    while day <= end_date:
        for shift in shift_types:
            st = combine_datetime(day, shift.start_time)
            et = combine_datetime(add_days(day, 1) if shift.end_time <= shift.start_time else day, shift.end_time)
            windows.append({"shift_type": shift.name, "start": st, "end": et})
        day = add_days(day, 1)

    return windows

def has_overlap(machine, mould, start, end):
    filters = {"status": ["!=", "Cancelled"], "workstation": machine}
    if mould:
        filters["mould"] = mould

    wos = frappe.get_all(
        "Work Order",
        filters=filters,
        fields=["actual_start_date", "actual_end_date", "planned_start_date", "planned_end_date"]
    )

    for wo in wos:
        st = wo.actual_start_date or wo.planned_start_date
        et = wo.actual_end_date or wo.planned_end_date
        if st and et and st < end and et > start:
            return True
    return False

def allocate_qty_in_window(remaining, start, end, pcs_hr, utilization):
    hours = (end - start).total_seconds() / 3600
    usable_hours = hours * (utilization / 100)
    allowed_qty = int(min(remaining, usable_hours * pcs_hr))
    actual_end = start + timedelta(hours=(allowed_qty / pcs_hr)) if allowed_qty > 0 else start
    return allowed_qty, actual_end

def resolve_warehouses(company, item_code):
    fg = frappe.db.get_value("Item Default", {"parent": item_code, "company": company}, "default_warehouse") \
        or frappe.db.get_single_value("Manufacturing Settings", "default_finished_goods_warehouse") \
        or frappe.db.get_value("Warehouse", {"warehouse_name": ["like", "%Finished Goods%"], "company": company, "disabled": 0}, "name")
    
    wip = frappe.db.get_single_value("Manufacturing Settings", "default_wip_warehouse") \
        or frappe.db.get_value("Warehouse", {"warehouse_name": ["like", "%Work In Progress%"], "company": company, "disabled": 0}, "name")

    if not fg or not wip:
        frappe.throw(_("FG / WIP warehouse not configured for company {0}").format(company))
    
    return fg, wip

def get_last_wo_end(machine, mould=None):
    filters = {"status": ["!=", "Cancelled"], "workstation": machine}
    if mould:
        filters["mould"] = mould

    wo = frappe.get_all(
        "Work Order",
        filters=filters,
        fields=["actual_end_date", "planned_end_date"],
        order_by="COALESCE(actual_end_date, planned_end_date) desc",
        limit=1
    )
    if not wo:
        return None
    return wo[0].actual_end_date or wo[0].planned_end_date

def create_work_order(doc_args, operations_args):
    wo = frappe.new_doc("Work Order")
    for k, v in doc_args.items():
        setattr(wo, k, v)
    wo.flags.ignore_permissions = True
    wo.insert()

    for op_args in operations_args:
        op = wo.append("operations", {})
        for k, v in op_args.items():
            setattr(op, k, v)
    wo.save(ignore_permissions=True)
    return wo.name

# -----------------------------
# API: VALIDATE CAPACITY
# -----------------------------
@frappe.whitelist()
def validate_capacity(payload):
    payload = frappe.parse_json(payload)
    utilization = flt(payload.get("production_utilization", 100))
    lines = payload.get("lines", [])
    result = []

    for ln in lines:
        pcs_hr = pcs_per_hour(ln["cycle_time"], ln["cavity"])
        required_hours = ln["schedule_qty"] / pcs_hr
        windows = get_shift_windows(payload["plan_start_date"], payload["plan_end_date"])
        available = sum((w["end"] - w["start"]).total_seconds()/3600 * utilization/100 for w in windows)

        result.append({
            "rowKey": ln["row_key"],
            "pcs_per_hour": round(pcs_hr, 2),
            "required_hours": round(required_hours, 2),
            "available_hours": round(available, 2),
            "capacity_gap": round(available - required_hours, 2),
            "ok": required_hours <= available
        })
    return result

# -----------------------------
# API: PREVIEW SCHEDULE
# -----------------------------
@frappe.whitelist()
def preview_capacity_plan(payload):
    payload = frappe.parse_json(payload)
    utilization = flt(payload.get("production_utilization", 100))
    ln = payload["lines"][0]

    pcs_hr = pcs_per_hour(ln["cycle_time"], ln["cavity"])
    remaining = flt(ln["schedule_qty"])
    windows = get_shift_windows(payload["plan_start_date"], payload["plan_end_date"])

    current_start = get_last_wo_end(ln["machine"], ln.get("mould")) or combine_datetime(getdate(payload['plan_start_date']), time(6,0))
    preview = []
    shift_no = 1

    for w in windows:
        st, et = w["start"], w["end"]
        if remaining <= 0:
            break
        st = max(st, current_start)
        if st >= et:
            continue

        allowed, actual_end = allocate_qty_in_window(remaining, st, et, pcs_hr, utilization)
        if allowed <= 0:
            continue

        preview.append({
            "shift_no": shift_no,
            "start": st,
            "end": actual_end,
            "planned_hours": round(allowed/pcs_hr, 2),
            "qty": round(allowed, 2)
        })
        remaining -= allowed
        current_start = actual_end
        shift_no += 1

    return [{"row_key": ln["row_key"], "preview": preview}]

# -----------------------------
# API: CREATE WORK ORDERS
# -----------------------------
@frappe.whitelist()
def create_work_orders_from_mss(payload):
    payload = frappe.parse_json(payload)
    utilization = flt(payload.get("production_utilization", 100))
    created = []

    for ln in payload.get("lines", []):
        pcs_hr = pcs_per_hour(ln["cycle_time"], ln["cavity"])
        remaining = flt(ln["schedule_qty"])
        so = frappe.get_doc("Sales Order", ln.get("sales_order"))
        fg, wip = resolve_warehouses(so.company, ln["item_code"])
        windows = get_shift_windows(payload["plan_start_date"], payload.get("plan_end_date"))

        current_start = get_last_wo_end(ln["machine"], ln.get("mould")) or combine_datetime(getdate(payload['plan_start_date']), time(6,0))

        bom_ops = frappe.get_all(
            "BOM Operation",
            filters={"parent": ln.get("bom_no")},
            fields=["operation", "workstation", "description", "time_in_mins", "workstation_type"],
            order_by="idx asc"
        )

        operations_args = []
        for op in bom_ops:
            operations_args.append({
                "workstation": op.workstation,
                "operation": op.operation,
                "bom_no": ln.get("bom_no"),
                "description": op.description,
                "workstation_type": op.workstation_type,
                "status": "Pending",
                "time_in_mins": op.time_in_mins or 1
            })

        for w in windows:
            st, et = w["start"], w["end"]
            if remaining <= 0:
                break
            st = max(st, current_start)
            if st >= et or has_overlap(ln["machine"], ln.get("mould"), st, et):
                continue

            used, actual_end = allocate_qty_in_window(remaining, st, et, pcs_hr, utilization)
            if used <= 0:
                continue

            doc_args = {
                "company": so.company,
                "production_item": ln["item_code"],
                "bom_no": ln["bom_no"],
                "mould": ln.get("mould"),
                "sales_order": ln.get("sales_order"),
                "fg_warehouse": fg,
                "wip_warehouse": wip,
                "qty": used,
                "planned_start_date": st,
                "planned_end_date": actual_end
            }

            wo_name = create_work_order(doc_args, operations_args)
            created.append(wo_name)
            remaining -= used
            current_start = actual_end

        if remaining > 0:
            frappe.throw(_("Insufficient capacity for {0}").format(ln["item_code"]))

    return {"created_work_orders": created}

########################################################################################################################        
##### -------------------- Level 7: Work Orders for Blanket Orders -------------------- #####
@frappe.whitelist()
def get_work_orders_for_so(so_list: str | list = None):
    
    if not so_list:
        return []

    if isinstance(so_list, str):
        try:
            so_list = json.loads(so_list)
        except Exception:
            so_list = [s.strip() for s in so_list.split(",") if s.strip()]

    if not so_list:
        return []

    placeholders = ",".join(["%s"] * len(so_list))

    sql = f"""
        SELECT
            name AS wo_name,
            production_item,
            qty AS wo_qty,
            status,
            material_transferred_for_manufacturing,
            disassembled_qty,
            bom_no,
            company,
            IFNULL(produced_qty, 0) AS produced_qty,
            sales_order,
            fg_warehouse,
            scrap_warehouse,
            wip_warehouse,
            planned_start_date, 
            planned_end_date,
            expected_delivery_date,
            stock_uom 
        FROM `tabWork Order`
        WHERE sales_order IN ({placeholders}) 
        ORDER BY planned_start_date DESC
    """
    work_orders = frappe.db.sql(sql, tuple(so_list), as_dict=True) or []

    result = []
    
    def format_dt(dt):
        if dt:
            return get_datetime(dt).replace(microsecond=0).strftime("%Y-%m-%d %H:%M:%S")
        return ""

    for wo in work_orders:
        
        result.append({
            "wo_name": wo.wo_name,
            "so_name": wo.sales_order,
            "production_item": wo.production_item,
            "wo_qty": flt(wo.wo_qty),
            "produced_qty": flt(wo.produced_qty), 
            "status": wo.status,
            "material_transferred_for_manufacturing": wo.material_transferred_for_manufacturing,
            "disassembled_qty": flt(wo.disassembled_qty),
            "bom_no": wo.bom_no,
            "company": wo.company,
            "fg_warehouse": wo.fg_warehouse,
            "scrap_warehouse": wo.scrap_warehouse,
            "wip_warehouse": wo.wip_warehouse,
            "planned_start_date": format_dt(wo.planned_start_date),
            "planned_end_date": format_dt(wo.planned_end_date),
            "expected_delivery_date": format_dt(wo.expected_delivery_date),
            "stock_uom": wo.stock_uom, 
        })
        
    return result

##### -------------------- Level 8: Job Cards for Work Orders -------------------- #####
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

    job_cards = frappe.db.sql(
        f"""
        SELECT
            name AS job_card,
            status AS job_card_status,
            operation,
            workstation,
            work_order,
            production_item,
            mould,
            expected_start_date,
            expected_end_date,
            time_required,
            total_completed_qty,
            process_loss_qty,
            wip_warehouse,
            quality_inspection,
            posting_date,
            bom_no
        FROM `tabJob Card`
        WHERE work_order IN ({placeholders})
        ORDER BY work_order, name
        """,
        tuple(wo_list),
        as_dict=True
    ) or []

    result = []

    for jc in job_cards:
        jc_items = frappe.db.get_all(
            "Job Card Item",
            filters={"parent": jc["job_card"]},
            fields=["item_code", "item_name", "required_qty AS qty"]
        ) or []

        if not jc_items:
            jc_items = [{"item_code": "", "item_name": "", "qty": 0}]

        for ji in jc_items:
            consumed = _get_jobcard_consumed_for_wo(jc["work_order"], ji["item_code"])
            bin_tot = _get_bin_totals(ji["item_code"]) or {}

            result.append({
                **jc,
                "rm_item_code": ji["item_code"],
                "rm_item_name": ji["item_name"],
                "required_qty": ji["qty"],
                "available_qty": bin_tot.get("actual_qty", 0),
                "consumed_qty": consumed
            })

    return result

##### -------------------- Level 9: Production Summary -------------------- #####
@frappe.whitelist()
def get_production_control_dashboard(customer = None, month: str = None, year: str = None):
    if not customer:
        return []

    rows = frappe.db.sql("""
        SELECT
            bo.name AS blanket_order,
            boi.name AS bo_item,
            boi.item_code,
            boi.item_name,
            boi.qty AS order_qty,
            so.name AS sales_order,
            bom.name AS bom_no,
            wo.name AS work_order,
            wo.status AS wo_status,
            wo.qty AS wo_qty,
            wo.produced_qty,
            wo.planned_start_date,
            wo.planned_end_date,
            jc.name AS job_card,
            jc.status AS job_card_status,
            jc.start_time,
            jc.end_time,
            dn.name AS delivery_note,
            dn.posting_date

        FROM `tabBlanket Order Item` boi
        INNER JOIN `tabBlanket Order` bo
            ON bo.name = boi.parent AND bo.docstatus = 1

        LEFT JOIN `tabSales Order Item` soi
            ON soi.blanket_order = bo.name
            AND soi.item_code = boi.item_code
        LEFT JOIN `tabSales Order` so
            ON so.name = soi.parent AND so.docstatus = 1

        LEFT JOIN `tabBOM` bom
            ON bom.item = boi.item_code
            AND bom.is_active = 1

        LEFT JOIN `tabWork Order` wo
            ON wo.sales_order = so.name
            AND wo.production_item = boi.item_code
            AND wo.docstatus = 1

        LEFT JOIN `tabJob Card` jc
            ON jc.work_order = wo.name
            AND jc.docstatus = 1

        LEFT JOIN `tabDelivery Note Item` dni
            ON dni.against_sales_order = so.name
            AND dni.item_code = boi.item_code
        LEFT JOIN `tabDelivery Note` dn
            ON dn.name = dni.parent
            AND dn.docstatus = 1

        WHERE bo.customer = %(customer)s
        ORDER BY bo.name, boi.idx
    """, {"customer": customer}, as_dict=True)

    return normalize(rows)
def normalize(rows):
    data = {}

    for r in rows:
        key = (r.blanket_order, r.bo_item)

        if key not in data:
            data[key] = {
                "blanket_order": r.blanket_order,
                "item_code": r.item_code,
                "item_name": r.item_name,
                "order_qty": flt(r.order_qty),
                "sales_order": r.sales_order,
                "bom": r.bom_no,
                "work_order": r.work_order,
                "wo_status": r.wo_status,
                "produced_qty": flt(r.produced_qty),
                "job_cards": [],
                "delivery_notes": [],
                "timeline": []
            }

            if r.planned_start_date and r.planned_end_date:
                data[key]["timeline"].append({
                    "label": "Work Order",
                    "start": r.planned_start_date,
                    "end": r.planned_end_date
                })

        if r.job_card and r.start_time and r.end_time:
            data[key]["job_cards"].append({
                "name": r.job_card,
                "status": r.job_card_status
            })

            data[key]["timeline"].append({
                "label": f"Job Card {r.job_card}",
                "start": r.start_time,
                "end": r.end_time
            })

        if r.delivery_note:
            data[key]["delivery_notes"].append(r.delivery_note)

    result = []
    for row in data.values():
        row["status"] = compute_status(row)
        result.append(row)

    return result
def compute_status(r):
    if not r["bom"]:
        return "BOM Missing"

    if not r["work_order"]:
        return "Work Order Not Created"

    if r["produced_qty"] >= r["order_qty"]:
        return "Production Completed"

    if r["job_cards"]:
        return "In Production"

    return "Planned"