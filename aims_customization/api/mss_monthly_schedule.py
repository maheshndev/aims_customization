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

    if (month or year) and not date_filter:
        return []

    if date_filter:
        if date_filter["type"] in ("month_year", "year"):
            sql += """
                AND from_date <= %s
                AND (to_date >= %s OR to_date IS NULL)
            """
            params.extend([date_filter["end"], date_filter["start"]])
        elif date_filter["type"] == "month_only":
            sql += """
                AND (
                    (MONTH(from_date) <= MONTH(to_date) AND MONTH(from_date) <= %s AND MONTH(to_date) >= %s)
                    OR (MONTH(from_date) > MONTH(to_date) AND (%s >= MONTH(from_date) OR %s <= MONTH(to_date)))
                    OR (to_date IS NULL AND MONTH(from_date) <= %s)
                )
            """
            m = date_filter["month"]
            params.extend([m, m, m, m, m])

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
            bo.from_date,
            bo.to_date,
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
    # normalize empty values
    month = month or None
    year = year or None

    date_filter = get_date_range(month, year)

    if (month or year) and not date_filter:
        return []

    if date_filter:

         # CASE 1: Month + Year
        if date_filter["type"] == "month_year":
            sql += """
                AND bo.from_date <= %s
                AND (bo.to_date >= %s OR bo.to_date IS NULL)
            """
            params.extend([date_filter["end"], date_filter["start"]])
         # CASE 2: Only Year
        elif date_filter["type"] == "year":
            sql += """
                AND bo.from_date <= %s
                AND (bo.to_date >= %s OR bo.to_date IS NULL)
            """
            params.extend([date_filter["end"], date_filter["start"]])
                # CASE 3: Only Month (ANY YEAR, cross-year safe)
        elif date_filter["type"] == "month_only":
            sql += """
                AND (
                    (
                        MONTH(bo.from_date) <= MONTH(bo.to_date)
                        AND MONTH(bo.from_date) <= %s
                        AND MONTH(bo.to_date) >= %s
                    )
                    OR
                    (
                        MONTH(bo.from_date) > MONTH(bo.to_date)
                        AND (
                            %s >= MONTH(bo.from_date)
                            OR %s <= MONTH(bo.to_date)
                        )
                    )
                    OR
                    (
                        bo.to_date IS NULL
                        AND MONTH(bo.from_date) <= %s
                    )
                )
            """
            m = date_filter["month"]
            params.extend([m, m, m, m, m])


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
        bo_names = [r["bo_name"] for r in rows]
        placeholders = ", ".join(["%s"] * len(bo_names))
        
        consumed = frappe.db.sql(f"""
            SELECT
                soi.blanket_order,
                soi.item_code,
                SUM(soi.qty) AS consumed_qty
            FROM `tabSales Order Item` soi
            JOIN `tabSales Order` so ON so.name = soi.parent
            WHERE soi.blanket_order IN ({placeholders})
              AND so.docstatus < 2
            GROUP BY soi.blanket_order, soi.item_code
        """, tuple(bo_names), as_dict=True)

        for c in consumed:
            key = (c["blanket_order"], c["item_code"])
            if key in bo_item_map:
                bo_item_map[key] = flt(c["consumed_qty"])

    # Distribution logic: FIFO-style across multiple lines for the same item in a BO
    # We maintain the pool of consumed quantity and subtract as we go.
    consumed_pool = bo_item_map.copy()

    result = []
    # Make sure rows are ordered by idx as fetched from SQL
    for r in rows:
        key = (r["bo_name"], r["item_code"])
        order_qty = flt(r["order_qty"])
        
        # How much of this row is already "consumed"?
        pool_qty = consumed_pool.get(key, 0)
        
        # Amount to subtract from THIS line
        subtracted = min(order_qty, pool_qty)
        
        # Update pool
        consumed_pool[key] = pool_qty - subtracted
        
        remaining_bo_qty = order_qty - subtracted
        row_consumed_qty = subtracted

        if remaining_bo_qty <= 0:
            continue

        result.append({
            "customer": r["customer"],
            "bo_name": r["bo_name"],
            "order_date": r["order_date"],
            "from_date":r["from_date"],
            "to_date": r["to_date"],
            "item_code": r["item_code"],
            "item_name": r["item_name"],
            "order_qty": order_qty,
            "remaining_bo_qty": remaining_bo_qty,
            "schedule_qty": 0,
            "consumed_qty": row_consumed_qty,
            "rate": flt(r["rate"]),
            "idx": r["idx"], # Added idx
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
        
        first_item = bo_items[0]
        so.transaction_date = first_item.get("transaction_date") or nowdate()
        so.delivery_date = first_item.get("delivery_date") or nowdate()
        so.po_no = first_item.get("po_no")
        so.po_date = first_item.get("po_date")
        
        if first_item.get("customer_po_attachment"):
            so.customer_po_attachment = first_item.get("customer_po_attachment")
        
        so.currency = getattr(bo, "currency", None) or frappe.get_value("Company", bo.company, "default_currency") or "USD"
        so.status = "Draft"

        for it in bo_items:
            item_doc = frappe.get_doc("Item", it.get("item_code"))

            warehouse = it.get("warehouse")
            if not warehouse:
                try:
                    # Use the robust helper to find FG warehouse
                    warehouse, _ = resolve_warehouses(bo.company, it.get("item_code"))
                except Exception:
                    # Fallback to item default with company filter if resolve_warehouses fails
                    warehouse = frappe.get_value("Item Default", {"parent": it.get("item_code"), "company": bo.company}, "default_warehouse") or ""
            
            rate = it.get("rate") or item_doc.standard_rate or 0

            so.append("items", {
                "item_code": it.get("item_code"),
                "item_name": item_doc.item_name,
                "qty": it.get("schedule_qty"),
                "rate": rate,
                "delivery_date": so.delivery_date,
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
def get_sales_orders(search_text: str = None, month: str = None, year: str =None, customer: str = None, blanket_items: list | str = None,  limit: int = 200 ):
     
    columns = """
        DISTINCT
        so.name,
        so.customer,
        so.customer_name,
        so.transaction_date,
        so.delivery_date,
        so.status,
        so.total_qty,
        (SELECT GROUP_CONCAT(DISTINCT sub_soi.blanket_order SEPARATOR ', ') FROM `tabSales Order Item` sub_soi WHERE sub_soi.parent = so.name AND sub_soi.blanket_order IS NOT NULL AND sub_soi.blanket_order != '') as blanket_order
    """
    
    table = "`tabSales Order` so"
    where_clause = "WHERE 1 = 1"
    
    # Check if we need to join items table for filtering
    has_bo_filter = False
    params = []

    if blanket_items:
        if isinstance(blanket_items, str):
            try:
                blanket_items = json.loads(blanket_items)
            except Exception:
                blanket_items = []
        
        bo_names = set()
        for i in blanket_items:
            if isinstance(i, dict):
                bo_names.add(i.get("bo_name") or i.get("blanket_order"))
            elif isinstance(i, str):
                bo_names.add(i)
        
        bo_names = [b for b in bo_names if b]

        if bo_names:
            has_bo_filter = True
            # Join with items table
            table += " JOIN `tabSales Order Item` soi ON soi.parent = so.name"
            
            placeholders = ", ".join(["%s"] * len(bo_names))
            where_clause += f" AND soi.blanket_order IN ({placeholders})"
            params.extend(bo_names)

    sql = f"SELECT {columns} FROM {table} {where_clause}"

    if customer:
        sql += " AND so.customer = %s"
        params.append(customer)

    if search_text:
        sql += " AND (so.name LIKE %s OR so.customer_name LIKE %s)"
        like = f"%{search_text}%"
        params.extend([like, like])

    date_filter = get_date_range(month, year)

    if (month or year) and not date_filter:
        return []

    if date_filter:
        if date_filter["type"] in ("month_year", "year"):
            sql += " AND so.transaction_date BETWEEN %s AND %s"
            params.extend([date_filter["start"], date_filter["end"]])
            
        elif date_filter["type"] == "month_only":
            sql += " AND MONTH(so.transaction_date) = %s"
            params.append(month)
   
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
                soi.bom_no,
                soi.idx
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
            "blanket_order": r.get("blanket_order") or "",
            "month": r["transaction_date"].strftime("%B-%Y") if r["transaction_date"] else "",
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
        fields=["parent", "item_code", "qty", "bom_no", "blanket_order", "delivery_date"]
    )

    def process_item_recursive(item_code, required_qty, so_name, customer, blanket_order, delivery_date=None, forced_bom=None, level=0, processed_items=None):

        if processed_items is None:
            processed_items = set()
        
        # Avoid infinite recursion (though BOMs shouldn't have circular refs)
        item_key = (item_code, forced_bom or "")
        if item_key in processed_items:
            return []
        processed_items.add(item_key)

        bom_filters = {"name": forced_bom} if forced_bom else {
            "item": item_code,
            "is_active": 1,
            "is_default": 1
        }

        boms = frappe.get_all(
            "BOM",
            filters=bom_filters,
            fields=["name as bom_no", "bom_type", "quantity as bom_qty"],
            limit_page_length=1 if forced_bom else 0
        )

        if not boms:
            return []

        item_data = frappe.db.get_value(
            "Item",
            item_code,
            [
                "pcs_wt", "runner_wt", "shot_wt",
                "gross_wt", "cycle_time", "cavity", "item_name"
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

        node_results = []
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

            # Check existing Work Orders for this SO + Item to calculate remaining qty
            wos = frappe.get_all("Work Order", {
                "sales_order": so_name,
                "production_item": item_code,
                "docstatus": ["!=", 2]  # Exclude cancelled
            }, ["qty"])
            
            planned_qty = sum(flt(w.qty) for w in wos)
            remaining_qty = max(0, flt(required_qty) - planned_qty)

            node_results.append({
                "sales_order": so_name,
                "blanket_order": blanket_order or "",
                "customer": customer,
                "item_code": item_code,
                "item_name": item_data.get("item_name"),
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
                "total_so_qty": required_qty,
                "planned_qty": planned_qty,
                "required_for_selected_qty": remaining_qty,
                "has_work_order": remaining_qty <= 0 and planned_qty > 0,
                "level": level,
                "delivery_date": delivery_date
            })

            # Recursively process sub-assemblies
            for b_item in bom_items:
                # Check if this item has a BOM (it's a sub-assembly)
                sub_bom = frappe.db.get_value("BOM", {"item": b_item.rm_item_code, "is_active": 1, "is_default": 1}, "name")
                if sub_bom:
                    # Calculate required qty for sub-assembly
                    # (required_qty / bom_qty) * qty_per_bom
                    sub_req_qty = (required_qty / (flt(bom.bom_qty) or 1.0)) * flt(b_item.qty_per_bom)
                    sub_assemblies = process_item_recursive(
                        item_code=b_item.rm_item_code,
                        required_qty=sub_req_qty,
                        so_name=so_name,
                        customer=customer,
                        blanket_order=blanket_order,
                        delivery_date=delivery_date,
                        level=level + 1,
                        processed_items=processed_items
                    )

                    node_results.extend(sub_assemblies)
        
        return node_results

    for so_item in so_items:
        result.extend(process_item_recursive(
            item_code=so_item.item_code,
            required_qty=flt(so_item.qty or 0),
            so_name=so_item.parent,
            customer=customer_map.get(so_item.parent),
            blanket_order=so_item.blanket_order,
            delivery_date=so_item.delivery_date,
            forced_bom=so_item.bom_no,
            level=0
        ))


    return result

##### -------------------- Level 5: Raw Materials for BOMs Section -------------------- #####
@frappe.whitelist()
def get_raw_materials_for_boms(boms: list = None):
   
    if not boms:
        return []

    if isinstance(boms, str):
        boms = json.loads(boms)

    result = []

    for b in boms:
        if not isinstance(b, dict):
            continue

        bom_no = b.get("bom_no")
        fg_item = b.get("item_code")
        sales_order = b.get("sales_order") or b.get("name") 
        blanket_order = b.get("blanket_order") or ""
        req_qty = flt(b.get("required_for_selected_qty"))

        if not bom_no or req_qty <= 0:
            continue

        bom_qty = flt(
            frappe.db.get_value("BOM", bom_no, "quantity") or 1.0
        )
    
        components = frappe.db.sql("""
            SELECT
                item_code,
                item_name,
                stock_qty AS qty,
                uom,
                rm_percentage
            FROM `tabBOM Item`
            WHERE parent=%s
        """, bom_no, as_dict=True)

        for comp in components:
            qty_per_bom_unit = flt(comp.qty)
            required_qty = (req_qty / bom_qty) * qty_per_bom_unit

            bin_tot = _get_bin_totals(comp.item_code)

            available = flt(bin_tot.get("actual_qty", 0))
            projected = flt(bin_tot.get("projected_qty", 0))
            balance = available - required_qty

            result.append({
                # 🔹 Separation keys
                "bom_no": bom_no or "",
                "fg_item": fg_item or "",
                "sales_order": sales_order or "",
                "blanket_order": blanket_order or "",

                # 🔹 RM details
                "rm_item_code": comp.item_code or "",
                "rm_item_name": comp.item_name or "",
                "stock_uom": comp.uom or "",
                "qty_per_bom_unit": qty_per_bom_unit or 0,
                "rm_percentage": flt(comp.rm_percentage) or 0,

                # 🔹 Qty details
                "required_qty": round(required_qty, 6) or 0,
                "available_qty": available or 0,
                "projected_qty": projected or 0,
                "balance_qty": round(balance, 6) or 0,
                "is_sufficient": balance >= 0 ,
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
    if isinstance(val, str):
        try:
            # Handle HH:mm:ss or HH:mm
            parts = [int(x) for x in val.split(":")]
            return time(*parts)
        except Exception:
            return None
    return None

def combine_datetime(date, t):
    return datetime.combine(date, _to_time(t))

def pcs_per_hour(cycle_time, cavity):
    cycle = flt(cycle_time)
    cavity = max(1, cint(cavity))
    if cycle <= 0:
        # Fallback to a very small rate or return 0 instead of throwing to avoid breaking the tool
        return 0
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

    if not shift_types:
        # Fallback to a default 24h shift if none defined in the system
        shift_types = [frappe._dict({
            "name": "Default 24h",
            "start_time": "00:00:00",
            "end_time": "23:59:59"
        })]

    day = start_date
    while day <= end_date:
        for shift in shift_types:
            st = combine_datetime(day, shift.start_time)
            et = combine_datetime(add_days(day, 1) if shift.end_time <= shift.start_time else day, shift.end_time)
            windows.append({"shift_type": shift.name, "start": st, "end": et})
        day = add_days(day, 1)

    return windows

def has_overlap(machine, mould, start, end):
    filters = {"status": ["not in", ["Cancelled", "Completed"]], "workstation": machine}
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
    """
    Get the last work order end time for machine and/or mould.
    Excludes Cancelled and Completed work orders.
    Returns: dict with machine_end, mould_end, and latest_end
    """
    # 1. Check Machine Availability
    machine_end = None
    if machine:
        wo_m = frappe.get_all(
            "Work Order",
            filters={"status": ["not in", ["Cancelled", "Completed"]], "workstation": machine},
            fields=["actual_end_date", "planned_end_date"],
            order_by="COALESCE(actual_end_date, planned_end_date) desc",
            limit=1
        )
        if wo_m:
            machine_end = wo_m[0].actual_end_date or wo_m[0].planned_end_date

    # 2. Check Mould Availability
    mould_end = None
    if mould:
        wo_mod = frappe.get_all(
            "Work Order",
            filters={"status": ["not in", ["Cancelled", "Completed"]], "mould": mould},
            fields=["actual_end_date", "planned_end_date"],
            order_by="COALESCE(actual_end_date, planned_end_date) desc",
            limit=1
        )
        if wo_mod:
            mould_end = wo_mod[0].actual_end_date or wo_mod[0].planned_end_date

    # Return detailed availability info
    latest_end = None
    if machine_end and mould_end:
        latest_end = max(machine_end, mould_end)
    else:
        latest_end = machine_end or mould_end
    
    return {
        "machine_end": machine_end,
        "mould_end": mould_end,
        "latest_end": latest_end
    }

@frappe.whitelist()
def get_smart_schedule_preview(lines, plan_start_date=None, plan_end_date=None):
    """
    Check availability of machines and moulds for scheduling.
    Excludes Cancelled and Completed work orders.
    Defaults to today if plan_start_date is not provided.
    If plan_end_date is provided, checks for overlaps within the period.
    """
    lines = frappe.parse_json(lines)
    result = []
    
    # Defaults - use today if not provided
    now = frappe.utils.now_datetime()
    plan_start = getdate(plan_start_date) if plan_start_date else now.date()
    plan_start_dt = datetime.combine(plan_start, time(6, 0))  # Default to 6 AM
    
    plan_end_dt = None
    if plan_end_date:
        plan_end = getdate(plan_end_date)
        plan_end_dt = datetime.combine(plan_end, time(22, 0)) # Default to 10 PM for end

    for ln in lines:
        machine = ln.get("machine")
        mould = ln.get("mould")
        item_code = ln.get("item_code")
        row_key = ln.get("rowKey")
        
        # Get availability info for machine and mould (historical/last end)
        availability = get_last_wo_end(machine, mould)
        machine_end = availability.get("machine_end")
        mould_end = availability.get("mould_end")
        latest_end = availability.get("latest_end")
        
        # Determine earliest available start time
        available_start = max(now, plan_start_dt)
        if latest_end and latest_end > available_start:
            available_start = latest_end
        
        # Build detailed reason
        reason_parts = []
        is_available = True
        
        # If plan_end_dt is provided, we check for ANY overlap in the period [plan_start_dt, plan_end_dt]
        if plan_end_dt:
            # Check machine overlap specifically
            if has_overlap(machine, None, plan_start_dt, plan_end_dt):
                reason_parts.append(f"Machine busy in this period")
                is_available = False
            
            # Check mould overlap specifically
            if mould and has_overlap(None, mould, plan_start_dt, plan_end_dt):
                reason_parts.append(f"Mould busy in this period")
                is_available = False
        else:
            # Fallback to existing logic comparing against available_start
            if machine_end and machine_end > available_start:
                reason_parts.append(f"Machine busy until {machine_end.strftime('%Y-%m-%d %H:%M')}")
                is_available = False
            
            if mould and mould_end and mould_end > available_start:
                reason_parts.append(f"Mould busy until {mould_end.strftime('%Y-%m-%d %H:%M')}")
                is_available = False
        
        if not reason_parts:
            # Also check if available_start is past plan_end_dt if provided
            if plan_end_dt and available_start > plan_end_dt:
                reason = "Not available in requested period"
                is_available = False
            else:
                reason = "Available Now"
        else:
            reason = "; ".join(reason_parts)
        
        result.append({
            "row_key": row_key,
            "item_code": item_code,
            "machine": machine,
            "mould": mould,
            "available_start": available_start.strftime('%Y-%m-%d %H:%M:%S') if available_start else None,
            "mould_available_from": mould_end.strftime('%Y-%m-%d %H:%M:%S') if mould_end else None,
            "machine_available_from": machine_end.strftime('%Y-%m-%d %H:%M:%S') if machine_end else None,
            "reason": reason,
            "is_available": is_available
        })

    return result

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
        try:
            pcs_hr = pcs_per_hour(ln["cycle_time"], ln["cavity"])
            required_hours = ln["schedule_qty"] / pcs_hr

            windows = get_shift_windows(payload["plan_start_date"], payload["plan_end_date"])
            
            custom_start_time = payload.get("plan_start_time")
            start_dt_override = None
            if custom_start_time:
                 t_parts = [int(x) for x in str(custom_start_time).split(":")]
                 start_dt_override = combine_datetime(getdate(payload["plan_start_date"]), time(*t_parts[:3]))

            delivery_date = ln.get("delivery_date")
            delivery_date_dt = None
            if delivery_date:
                delivery_date_dt = combine_datetime(getdate(delivery_date), time(6, 0))

            available = 0.0
            for w in windows:
                st, et = w["start"], w["end"]
                
                # Effective start is max of window start, global start override, and SO delivery date
                effective_st = st
                if start_dt_override:
                     effective_st = max(effective_st, start_dt_override)
                if delivery_date_dt:
                     effective_st = max(effective_st, delivery_date_dt)
                
                if effective_st < et:
                     available += (et - effective_st).total_seconds() / 3600 * utilization / 100


            result.append({
                "rowKey": ln["row_key"],
                "pcs_per_hour": round(pcs_hr, 2),
                "required_hours": round(required_hours, 2),
                "available_hours": round(available, 2),
                "capacity_gap": round(available - required_hours, 2),
                "ok": required_hours <= available,
                "error": None
            })

        except Exception as e:
            result.append({
                "rowKey": ln["row_key"],
                "ok": False,
                "error": str(e)
            })

    return result


# -----------------------------
# API: PREVIEW SCHEDULE
# -----------------------------
@frappe.whitelist()
def preview_capacity_plan(payload):
    payload = frappe.parse_json(payload)
    ln = payload["lines"][0]

    try:
        utilization = flt(payload.get("production_utilization", 100))
        pcs_hr = pcs_per_hour(ln["cycle_time"], ln["cavity"])

        remaining = flt(ln["schedule_qty"])
        if remaining <= 0:
            return [{
                "row_key": ln["row_key"],
                "preview": [],
                "error": "Schedule Qty must be greater than zero"
            }]

        windows = get_shift_windows(payload["plan_start_date"], payload["plan_end_date"])
        custom_start_time = payload.get("plan_start_time")
        default_start = combine_datetime(getdate(payload["plan_start_date"]), time(6, 0))
        
        if custom_start_time:
             # If formatted as HH:mm:ss or HH:mm
             t_parts = [int(x) for x in str(custom_start_time).split(":")]
             default_start = combine_datetime(getdate(payload["plan_start_date"]), time(*t_parts[:3]))

        availability = get_last_wo_end(ln["machine"], ln.get("mould"))
        now = frappe.utils.now_datetime()
        current_start = availability.get("latest_end") or default_start
        current_start = max(now, current_start)

        delivery_date = ln.get("delivery_date")
        if delivery_date:
            delivery_date_dt = combine_datetime(getdate(delivery_date), time(6, 0))
            current_start = max(current_start, delivery_date_dt)


        preview = []
        shift_no = 1

        for w in windows:
            if remaining <= 0:
                break

            st, et = max(w["start"], current_start), w["end"]
            if st >= et:
                continue

            allowed, actual_end = allocate_qty_in_window(
                remaining, st, et, pcs_hr, utilization
            )

            if allowed <= 0:
                continue

            preview.append({
                "shift_no": shift_no,
                "planned_hours": round(allowed / pcs_hr, 2),
                "qty": allowed
            })

            remaining -= allowed
            current_start = actual_end
            shift_no += 1

        return [{
            "row_key": ln["row_key"],
            "preview": preview,
            "error": None
        }]

    except Exception as e:
        return [{
            "row_key": ln["row_key"],
            "preview": [],
            "error": str(e)
        }]

# -----------------------------
# API: CREATE WORK ORDERS
# -----------------------------
@frappe.whitelist()
def create_work_orders_from_mss(payload):
    payload = frappe.parse_json(payload)
    utilization = flt(payload.get("production_utilization", 100))

    created = []
    failed = []
    already_exists = []

    for ln in payload.get("lines", []):
        try:
            pcs_hr = pcs_per_hour(ln["cycle_time"], ln["cavity"])
            remaining = flt(ln["schedule_qty"])

            if remaining <= 0:
                failed.append(f"{ln['item_code']} – Qty must be > 0")
                continue

            so = frappe.get_doc("Sales Order", ln["sales_order"]) or ""
            fg, wip = resolve_warehouses(so.company, ln["item_code"])

            # Determine Windows
            windows = []
            selected_slots = ln.get("selected_slots")
            
            if selected_slots:
                for ss in selected_slots:
                    windows.append({
                        "start": get_datetime(ss["start"]),
                        "end": get_datetime(ss["end"]),
                        "qty": flt(ss.get("qty"))
                    })
            else:
                # Determine Strict Global Window
                start_date = getdate(payload["plan_start_date"])
                end_date = getdate(payload.get("plan_end_date") or start_date)
                
                def parse_t(t_val, default_h):
                    if not t_val: return time(default_h, 0)
                    parts = [int(x) for x in str(t_val).split(":")]
                    return time(*parts[:3])

                s_time = parse_t(payload.get("plan_start_time"), 6)
                e_time = parse_t(payload.get("plan_end_time"), 22)

                global_start = datetime.combine(start_date, s_time)
                global_end = datetime.combine(end_date, e_time)
                
                if global_end <= global_start:
                     if end_date == start_date:
                          global_end = datetime.combine(end_date, time(23, 59, 59, 0))

                all_shift_windows = get_shift_windows(start_date, end_date)
                for w in all_shift_windows:
                    s = max(w["start"], global_start)
                    e = min(w["end"], global_end)
                    if s < e:
                        windows.append({"start": s, "end": e})

            current_start = global_start if not selected_slots else None

            for w in windows:
                if remaining <= 0:
                    break

                st, et = w["start"], w["end"]
                
                # Check overlap with existing WOs
                if has_overlap(ln["machine"], ln.get("mould"), st, et):
                     # If the window is partially blocked, allocate_qty_in_window *might* handle it if we passed smart params
                     # but here we skip the whole window if there's any overlap?
                     # Better: Find the free gap within this window.
                     # However, simplicity: The UI guides the user to select a free slot.
                     # If they select a slot, it should be free.
                     # We will do a robust check: skip if overlap.
                     continue

                used, actual_end = allocate_qty_in_window(
                    remaining, st, et, pcs_hr, utilization
                )

                if used <= 0:
                    continue

                # Prepare Operations List
                operations_list = []
                if ln.get("bom_no"):
                     bom_ops = frappe.get_all(
                        "BOM Operation",
                        filters={"parent": ln["bom_no"]},
                        fields=["operation", "workstation", "time_in_mins", "batch_size", "sequence_id", "idx"],
                        order_by="idx"
                     )
                     
                     for op in bom_ops:
                         # Calculate time based on qty
                         batch_size = flt(op.batch_size) or 1.0
                         
                         # Standard BOM time calculation
                         time_required = (used / (flt(op.batch_size) or 1.0)) * flt(op.time_in_mins)
                         
                         # Capacity Override Logic:
                         # "set time in minutes after calculating capacity"
                         # We set the capacity-derived time for the operation that matches the main machine.
                         if op.workstation == ln["machine"]:
                             # Capacity Time = (Qty / Pcs Per Hour) * 60 mins
                             if pcs_hr > 0:
                                 time_required = (used / pcs_hr) * 60.0
                         
                         if time_required <= 0:
                             time_required = 0.01
                         
                         op_data = {
                             "operation": op.operation,
                             "workstation": op.workstation,
                             "time_in_mins": round(time_required, 2),
                             "bom_no": ln["bom_no"],  # Added BOM NO
                             "batch_size": batch_size,
                             "description": f"Operation {op.operation} from BOM {ln['bom_no']}",
                             "status": "Pending",
                             "completed_qty": 0
                         }
                         
                         # Attempt to fetch Workstation Type if available on Workstation
                         if op.workstation:
                             ws_type = frappe.db.get_value("Workstation", op.workstation, "workstation_type")
                             if ws_type:
                                 op_data["workstation_type"] = ws_type
                        
                         operations_list.append(op_data)

                # Bypassing SO-to-Item validation for SFGs:
                # If item is not directly in SO, we skip it in the insert() and set it via db_set afterward.
                actual_so = ln.get("sales_order")
                is_item_in_so = any(i.item_code == ln["item_code"] for i in so.items) if so else False

                wo_name = create_work_order(
                    {
                        "company": so.company if so else frappe.db.get_default("company"),
                        "production_item": ln["item_code"],
                        "bom_no": ln["bom_no"],
                        "mould": ln.get("mould") or "",
                        "sales_order": actual_so if is_item_in_so else "",
                        "fg_warehouse": fg,
                        "wip_warehouse": wip,
                        "qty": used or 1,
                        "planned_start_date": st,
                        "planned_end_date": actual_end,
                        "transfer_material_against": "Job Card",
                        "skip_transfer": 0
                    },
                    operations_args=operations_list
                )

                # Force set the SO link for display/tracking if it was skipped
                if actual_so and not is_item_in_so:
                    frappe.db.set_value("Work Order", wo_name, "sales_order", actual_so)

                # --- NEW: Direct Material Adjustment (Override BOM Items) ---
                modified_materials = ln.get("modified_items")
                if modified_materials:
                    # Clear existing WO Items and insert the new ones
                    frappe.db.sql("DELETE FROM `tabWork Order Item` WHERE parent = %s", wo_name)
                    for rm in modified_materials:
                        # Ratio adjustment: The modified_materials should be for the WHOLE SO.
                        # Since we might have split the WO, we need to scale the modified qty by (this_wo_qty / total_so_qty).
                        total_qty = flt(ln["schedule_qty"])
                        scaling = (used / total_qty) if total_qty > 0 else 1.0
                        
                        rm_qty = flt(rm.get("qty")) * scaling
                        
                        frappe.get_doc({
                            "doctype": "Work Order Item",
                            "parent": wo_name,
                            "parentfield": "required_items",
                            "parenttype": "Work Order",
                            "item_code": rm["item_code"],
                            "source_warehouse": rm.get("source_warehouse") or wip,
                            "required_qty": rm_qty
                        }).insert(ignore_permissions=True)



                created.append(wo_name)
                remaining -= used
                current_start = actual_end

            if remaining > 0:
                failed.append(
                    f"{ln['item_code']} – insufficient capacity ({remaining} remaining)"
                )

        except Exception as e:
            failed.append(f"{ln.get('item_code')} – {str(e)}")

    return {
        "created_work_orders": created,
        "failed": failed,
        "already_exists": already_exists
    }



# -----------------------------
# HELPERS: SLOT CALCULATION & SIMULATION
# -----------------------------
def get_availability_slots(machine, mould, start_dt, end_dt):
    """
    Returns a SORTED list of available time slots (start, end)
    within the requested [start_dt, end_dt] window.
    Merges overlapping time slots.
    """
    if not start_dt or not end_dt:
        return []

    # 1. Get Base Shift Windows (The "Potential" Time)
    shift_windows = get_shift_windows(start_dt.date(), end_dt.date())
    
    # Filter shift windows to be strictly within start_dt and end_dt
    potential_slots = []
    for sw in shift_windows:
        s = max(sw["start"], start_dt)
        e = min(sw["end"], end_dt)
        if s < e:
            potential_slots.append((s, e))

    if not potential_slots:
        # If we still have no potential slots, it might be due to window filtering
        # Try to provide at least one slot if start < end
        if start_dt < end_dt:
             potential_slots = [(start_dt, end_dt)]
        else:
             return []

    # 2. Get Busy Intervals (Existing Work Orders)
    busy_intervals = []
    
    # Machine Busy Time
    if machine:
        wos = frappe.get_all(
            "Work Order",
            filters={
                "status": ["not in", ["Cancelled", "Completed"]],
                "workstation": machine,
                "planned_end_date": [">", start_dt],
                "planned_start_date": ["<", end_dt]
            },
            fields=["planned_start_date", "planned_end_date", "actual_start_date", "actual_end_date"]
        )
        for w in wos:
            bs = w.actual_start_date or w.planned_start_date
            be = w.actual_end_date or w.planned_end_date
            if bs and be:
                busy_intervals.append((bs, be))

    # Mould Busy Time (if applicable)
    if mould:
        wos_m = frappe.get_all(
            "Work Order",
            filters={
                "status": ["not in", ["Cancelled", "Completed"]],
                "mould": mould,
                "planned_end_date": [">", start_dt],
                "planned_start_date": ["<", end_dt]
            },
            fields=["planned_start_date", "planned_end_date", "actual_start_date", "actual_end_date"]
        )
        for w in wos_m:
            bs = w.actual_start_date or w.planned_start_date
            be = w.actual_end_date or w.planned_end_date
            if bs and be:
                busy_intervals.append((bs, be))

    # Merge overlapping busy intervals
    if busy_intervals:
        busy_intervals.sort(key=lambda x: x[0])
        merged_busy = []
        if busy_intervals:
            curr_start, curr_end = busy_intervals[0]
            for i in range(1, len(busy_intervals)):
                next_start, next_end = busy_intervals[i]
                if next_start < curr_end:
                    curr_end = max(curr_end, next_end)
                else:
                    merged_busy.append((curr_start, curr_end))
                    curr_start, curr_end = next_start, next_end
            merged_busy.append((curr_start, curr_end))
        busy_intervals = merged_busy
    
    # Debug Logging
    if not busy_intervals and not potential_slots:
        pass # Handle later if needed
    else:
        # Only log if final slots will be empty or for specific machine
        frappe.log_error(
            message=f"Machine: {machine}, Mould: {mould}\nPotential: {potential_slots}\nBusy: {busy_intervals}",
            title="MSS Scheduler Debug: Slot Calc"
        )

    # 3. Subtract Busy from Potential
    # ...
    # We iterate through potential slots and "cut out" the busy parts
    final_slots = []
    
    for p_start, p_end in potential_slots:
        # Optimization: We can process this potential slot against busy intervals
        temp_slots = [(p_start, p_end)]
        
        for b_start, b_end in busy_intervals:
            new_temp = []
            for t_start, t_end in temp_slots:
                # No overlap
                if b_end <= t_start or b_start >= t_end:
                    new_temp.append((t_start, t_end))
                # Full overlap (busy covers whole slot)
                elif b_start <= t_start and b_end >= t_end:
                    continue 
                # Partial overlap
                else:
                    # Cut into pieces
                    if b_start > t_start:
                        new_temp.append((t_start, b_start))
                    if b_end < t_end:
                        new_temp.append((b_end, t_end))
            temp_slots = new_temp
        
        final_slots.extend(temp_slots)

    # 4. Merge Final Slots (if shifts overlapped or split adjacently)
    if not final_slots:
        return []
        
    final_slots.sort(key=lambda x: x[0])
    merged_final = []
    curr_s, curr_e = final_slots[0]
    
    for i in range(1, len(final_slots)):
         next_s, next_e = final_slots[i]
         if next_s <= curr_e: # Overlap or continuous
             curr_e = max(curr_e, next_e)
         else:
             merged_final.append((curr_s, curr_e))
             curr_s, curr_e = next_s, next_e
    merged_final.append((curr_s, curr_e))
    
    # Filter tiny slots (< 1 min)
    clean_slots = []
    for s, e in merged_final:
        if (e - s).total_seconds() >= 60:
            clean_slots.append((s, e))
            
    return clean_slots

def analyze_availability(machine, mould, production_params, start_dt, end_dt, utilization=90.0):
    """
    Returns ALL available slots in the window with calculated capacity for each.
    production_params: { item_code, cycle_time, cavity }
    Returns: list of {start, end, max_qty, duration_hrs, desc}
    """
    raw_slots = get_availability_slots(machine, mould, start_dt, end_dt)
    if not raw_slots:
        return []

    cycle = flt(production_params.get("cycle_time"))
    cavity = flt(production_params.get("cavity")) or 1.0
    
    # production rate (pcs / hr)
    rate = 0
    if cycle > 0:
        rate = (3600 / cycle) * cavity

    results = []
    for s_start, s_end in raw_slots:
        duration_hrs = (s_end - s_start).total_seconds() / 3600.0
        usable_hrs = duration_hrs * (utilization / 100.0)
        max_qty = round(usable_hrs * rate)

        fmt_s = s_start.strftime("%d-%m %H:%M")
        fmt_e = s_end.strftime("%d-%m %H:%M")
        
        desc = f"{fmt_s} to {fmt_e} ({round(duration_hrs,1)}h) | Max Qty: {max_qty}"
        
        results.append({
            "start": s_start,
            "end": s_end,
            "duration_hrs": round(duration_hrs, 1),
            "max_qty": max_qty,
            "desc": desc
        })

    return results


@frappe.whitelist()
def get_availability_slots_api(payload):
    """
    API WRAPPER: Returns ALL available slots with capacity info.
    Payload: { lines: [], plan_start_date, ..., production_utilization: 90 }
    """
    payload = frappe.parse_json(payload)
    lines = payload.get("lines", [])
    utilization = flt(payload.get("production_utilization", 90))
    
    # Determine Global Window
    start_date = getdate(payload.get("plan_start_date") or nowdate())
    end_date = getdate(payload.get("plan_end_date") or start_date) 
    
    def parse_t(t_val, default_h):
        if not t_val: return time(default_h, 0)
        t_str = str(t_val).strip()
        # Handle "07:30 AM" or "19:30"
        if " " in t_str:
            # Try parsing with AM/PM
            try:
                return datetime.strptime(t_str, "%I:%M %p").time()
            except Exception:
                try:
                    return datetime.strptime(t_str, "%H:%M %p").time()
                except Exception:
                    t_str = t_str.split(" ")[0] # Fallback to HH:mm
        
        try:
            parts = [int(x) for x in t_str.split(":")]
            return time(*parts[:3])
        except Exception:
            return time(default_h, 0)

    s_time = parse_t(payload.get("plan_start_time"), 0)
    e_time = parse_t(payload.get("plan_end_time"), 23)

    global_start = datetime.combine(start_date, s_time)
    global_end = datetime.combine(end_date, e_time)
    
    if global_end <= global_start:
         if end_date == start_date:
             global_end = datetime.combine(end_date, time(23, 59))

    resp = {}
    
    for ln in lines:
        rk = ln.get("rowKey") or ln.get("row_key")
        
        # Get Suggestions via analyze_availability
        slots = analyze_availability(
            ln.get("machine"),
            ln.get("mould"),
            {
                "item_code": ln.get("item_code"),
                "cycle_time": ln.get("cycle_time"),
                "cavity": ln.get("cavity")
            },
            global_start,
            global_end,
            utilization=utilization
        )
        
        # Serialize datetimes
        for s in slots:
            s["start"] = s["start"].strftime("%Y-%m-%d %H:%M:%S")
            s["end"] = s["end"].strftime("%Y-%m-%d %H:%M:%S")
        
        # Log empty slots for debugging
        if not slots:
             frappe.log_error(
                 message=f"No slots found for {rk}. machine={ln.get('machine')}, cycle={ln.get('cycle_time')}, utilization={utilization}, window={global_start} to {global_end}",
                 title="MSS Capacity Planner: No Slots"
             )

        resp[rk] = slots
        
    return resp



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
            stock_uom, 
            mould
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
            "mould": wo.mould
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
def get_production_control_dashboard(customer=None, month=None, year=None):
    if not customer:
        return {"ok": True, "data": []}
    
    month = cint(month) if month else None
    year = cint(year) if year else None
    date_range = get_date_range(month, year)

    rows = frappe.db.sql("""
        SELECT
            bo.name AS blanket_order,
            boi.item_code,
            boi.item_name,
            boi.qty AS order_qty,
            so.name AS sales_order,
            so.transaction_date
        FROM `tabBlanket Order Item` boi
        JOIN `tabBlanket Order` bo ON bo.name = boi.parent AND bo.docstatus = 1
        LEFT JOIN `tabSales Order Item` soi
            ON soi.blanket_order = bo.name
            AND soi.item_code = boi.item_code
        LEFT JOIN `tabSales Order` so ON so.name = soi.parent AND so.docstatus = 1
        WHERE bo.customer = %(customer)s
    """, {"customer": customer}, as_dict=True)

    result = []

    for r in rows:
        production = _get_production_totals(r.sales_order, r.item_code)
        dispatched = _get_dispatched_totals(r.sales_order, r.item_code)
        consumed = _get_so_consumed_qty(r.blanket_order, r.item_code)

        timeline = _build_timeline(r.sales_order, r.item_code, date_range)

        row = {
            "blanket_order": r.blanket_order,
            "item_code": r.item_code,
            "item_name": r.item_name,
            "order_qty": flt(r.order_qty),
            "produced_qty": flt(production["produced_qty"]),
            "dispatched_qty": flt(dispatched["qty"]),
            "consumed_qty": flt(consumed),
            "transaction_date": r.transaction_date,
            "balance_qty": flt(r.order_qty) - flt(production["produced_qty"]),
            "progress": _calc_progress(r.order_qty, production["produced_qty"]),
            "timeline": timeline,
            "status": compute_status({
                "produced_qty": flt(production["produced_qty"]),
                "order_qty": flt(r.order_qty)
            })
        }

        result.append(row)

    return {"ok": True, "data": result}


def compute_status(r):
    if r["produced_qty"] <= 0:
        return "Planned"

    if r["produced_qty"] < r["order_qty"]:
        return "In Production"

    if r["produced_qty"] >= r["order_qty"]:
        return "Production Completed"

    return "Unknown"

def _calc_progress(order_qty, produced_qty):
    if not order_qty:
        return 0
    return round((produced_qty / order_qty) * 100, 2)


def _build_timeline(sales_order, item_code, date_range):
    timeline = []

    wo_list = frappe.db.sql("""
        SELECT name, planned_start_date, planned_end_date
        FROM `tabWork Order`
        WHERE sales_order=%s
          AND production_item=%s
          AND docstatus=1
    """, (sales_order, item_code), as_dict=True)

    for wo in wo_list:

        # Work Order bar
        if wo.planned_start_date and wo.planned_end_date:
            timeline.append({
                "label": "Work Order",
                "start": str(wo.planned_start_date),
                "end": str(wo.planned_end_date)
            })


        # Job Card time logs
        job_logs = frappe.db.sql("""
            SELECT
                jc.name AS job_card,
                jctl.from_time,
                jctl.to_time
            FROM `tabJob Card` jc
            JOIN `tabJob Card Time Log` jctl
                ON jctl.parent = jc.name
            WHERE jc.work_order = %s
              AND jc.docstatus = 1
              AND jctl.from_time IS NOT NULL
              AND jctl.to_time IS NOT NULL
        """, (wo.name,), as_dict=True)

        for log in job_logs:
            timeline.append({
                "label": f"Job {log.job_card}",
                "start": str(log.from_time),
                "end": str(log.to_time)
            })


    return timeline
