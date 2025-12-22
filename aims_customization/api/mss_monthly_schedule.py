# aims_customization/api/mss_monthly_schedule.py
from __future__ import annotations
import json
from datetime import datetime, date, timedelta, time
import calendar
import frappe
from frappe.utils import nowdate, get_datetime, getdate, flt, time_diff_in_hours, get_last_day, now_datetime, get_first_day
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
    """
    Returns a tuple (start_date, end_date) or (month_only, year_only) flags.
    - month + year → filter that month & year
    - only year → filter all months of that year
    - only month → filter all years for that month
    - neither → None
    """
    m = None
    y = None

    # Parse year
    if year:
        try:
            y = int(year)
        except ValueError:
            return None

    # Parse month
    if month:
        s = str(month).strip()

        # Handle formats like Nov-2025, November-2025, 11-2025, 2025-11, 11/2025
        for sep in ("-", "/"):
            if sep in s:
                p1, p2 = s.split(sep, 1)
                if p1.isdigit() and len(p1) == 4:  # 2025-11
                    y = int(p1)
                    s = p2
                elif p2.isdigit() and len(p2) == 4:  # 11-2025
                    y = int(p2)
                    s = p1
                break

        # Numeric month
        if s.isdigit():
            m = int(s)
            if not (1 <= m <= 12):
                m = None
        else:
            # Text month (Nov / November)
            try:
                m = datetime.strptime(s[:3].title(), "%b").month
            except Exception:
                try:
                    m = list(calendar.month_name).index(s.title())
                except Exception:
                    m = None

    # Decide date filter
    if y and m:  # month + year
        start_date = f"{y}-{m:02d}-01"
        end_date = get_last_day(start_date)
        return {"type": "month_year", "start": start_date, "end": end_date}
    elif y and not m:  # only year
        start_date = f"{y}-01-01"
        end_date = f"{y}-12-31"
        return {"type": "year", "start": start_date, "end": end_date}
    elif m and not y:  # only month → filter month across all years
        return {"type": "month_only", "month": m}

    return None


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

# File: aims_customization/api/mss_monthly_schedule.py (No Change)

@frappe.whitelist()
def get_customers(search_text: str = None, customer_id: str = None, limit: int = 20):
    """
    Fetches customers, supporting search (LIKE) or lookup by ID.
    """
    sql = "SELECT name, customer_name FROM `tabCustomer` WHERE disabled=0"
    params = []

    if customer_id:
        # 1. Fetch a specific customer by ID
        sql += " AND name = %s"
        params.append(customer_id)
    elif search_text:
        # 2. Perform a LIKE search
        sql += " AND (name LIKE %s OR customer_name LIKE %s)"
        params.extend([f"%{search_text}%", f"%{search_text}%"])
        
        sql += " ORDER BY customer_name ASC LIMIT %s"
        params.append(limit)
    else:
        # 3. Default list (when input is empty or null)
        sql += " ORDER BY customer_name ASC LIMIT %s"
        params.append(limit)

    rows = frappe.db.sql(sql, tuple(params), as_dict=True) or []
    
    return [{"name": r["name"], "customer_name": r["customer_name"]} for r in rows]

# -------------------- Level 1: Blanket Orders --------------------

@frappe.whitelist()
def get_blanket_orders(search_text=None, customer=None, month=None, year=None, limit=500):
    
    # 1. Base Query to fetch Blanket Orders
    sql = """
        SELECT name, blanket_order_type, customer, customer_name, supplier, supplier_name,
               order_no, order_date, from_date, to_date, company, tc_name
        FROM `tabBlanket Order`
        WHERE docstatus = 1
    """
    params = []
    
    # Customer filter
    if customer:
        sql += " AND customer = %s"
        params.append(customer)

    # Search text filter
    if search_text:
        sql += " AND (name LIKE %s OR customer_name LIKE %s OR order_no LIKE %s)"
        params.extend([f"%{search_text}%", f"%{search_text}%", f"%{search_text}%"])

    # Date range filter
    date_filter = get_date_range(month, year)

    if date_filter:
        if date_filter["type"] in ("month_year", "year"):
            sql += " AND order_date BETWEEN %s AND %s"
            params.extend([date_filter["start"], date_filter["end"]])
        elif date_filter["type"] == "month_only":
            sql += " AND MONTH(order_date)=%s" 
            params.append(month) 

    # Limit & order
    sql += " ORDER BY order_date DESC LIMIT %s"
    params.append(limit)

    rows = frappe.db.sql(sql, tuple(params), as_dict=True) or []
    
    if not rows:
        return []

    # Get a list of BO names for the optimized lookups
    bo_names = [r["name"] for r in rows]
    placeholders = ", ".join(["%s"] * len(bo_names))

    # 2. Optimized Query for Total Blanket Quantity (Single Query)
    total_qty_map = {}
    total_qty_rows = frappe.db.sql(f"""
        SELECT parent, SUM(qty) AS total_qty
        FROM `tabBlanket Order Item`
        WHERE parent IN ({placeholders})
        GROUP BY parent
    """, tuple(bo_names), as_dict=True) or []

    for r in total_qty_rows:
        total_qty_map[r["parent"]] = flt(r["total_qty"])

    # 3. Optimized Query for Used Quantity (Single Query)
    # Filter by docstatus=1 (Submitted) on Sales Order to correctly calculate used quantity
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

    # 4. Combine and finalize result
    result = []
    for r in rows:
        bo_name = r["name"]
        
        total_bo_qty = total_qty_map.get(bo_name, 0.0)
        used_qty = used_qty_map.get(bo_name, 0.0)
        remaining_qty = total_bo_qty - used_qty

        # Add calculated/derived fields
        r["total_blanket_qty"] = total_bo_qty
        r["remaining_qty"] = remaining_qty
        r["month"] = _month_str_from_date(r["order_date"])
        
        result.append(r)

    return result


# -------------------- Level 2: Items for Blanket Orders --------------------
@frappe.whitelist()
def get_items_for_blanket_orders(bo_list: str | list):

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
            ["cavity", "pcs_wt", "runner_wt", "shot_wt", "weight_per_unit", "cycle_time"], as_dict=True
        ) or {}
        
        consumed_qty = _get_so_consumed_qty(line["bo_name"], line["item_code"])

        # NEW: Remaining qty
        remaining_qty =  line.get("order_qty") - consumed_qty

        result.append({

            "bo_name": line["bo_name"],
            "item_code": line["item_code"],
            "item_name": line["item_name"],
            "order_qty": line["order_qty"],
            "schedule_qty": 0,
            "rate": line["rate"],
            "bom_no": safe(line.get("bom_no")),
            "warehouse": safe(line.get("warehouse")),

            # Item attributes
            "cavity": safe(item_attrs.get("cavity")),
            "pcs_wt": safe(item_attrs.get("pcs_wt")),
            "runner_wt": safe(item_attrs.get("runner_wt")),
            "shot_wt": safe(item_attrs.get("shot_wt")),
            "cycle_time": safe(item_attrs.get("cycle_time")),
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
            "remaining_bo_qty": remaining_qty,
            "consumed_qty": consumed_qty
        })
        
    return result

@frappe.whitelist()
def get_blanket_orders_with_items(
    search_text=None,
    customer=None,
    month=None,
    year=None,
    limit=500
):
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

    # ---------------- CUSTOMER ----------------
    if customer:
        sql += " AND bo.customer = %s"
        params.append(customer)

    # ---------------- SEARCH ----------------
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

    # ---------------- DATE FILTER ----------------
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

    # ---------------- CONSUMED QTY (SO) ----------------
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

    # ---------------- FINAL RESULT ----------------
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

    # Group by Blanket Order
    orders = {}
    for it in items:
        bo_name = it.get("bo_name")
        if not bo_name:
            frappe.throw(f"Item {it.get('item_code')} is missing blanket_order")
        orders.setdefault(bo_name, []).append(it)

    created_sos = []
    skipped = []

    for bo_name, bo_items in orders.items():

        # ---- 1️⃣ Fetch Blanket Order ----
        bo = frappe.get_doc("Blanket Order", bo_name)

        # ---- 2️⃣ Check used quantity in all existing Sales Orders ----
        used_qty = frappe.db.sql("""
            SELECT SUM(soi.qty) AS qty
            FROM `tabSales Order Item` soi
            JOIN `tabSales Order` so ON so.name = soi.parent
            WHERE soi.blanket_order = %s AND so.docstatus < 2
        """, (bo_name,), as_dict=True)[0].qty or 0

        # Blanket Order total qty
        total_bo_qty = sum(row.qty for row in bo.items)

        # Remaining qty
        remaining_qty = total_bo_qty - used_qty

        # ---- 3️⃣ If nothing remaining → skip ----
        if remaining_qty <= 0:
            skipped.append({
                "blanket_order": bo_name,
                "reason": "Can not Create Sales Order because Fully consumed",
                "total_qty": total_bo_qty,
                "used_qty": used_qty,
                "remaining_qty": 0
            })
            continue

        # ---- 4️⃣ Create new Sales Order ----
        so = frappe.new_doc("Sales Order")
        so.customer = bo.customer
        so.company = bo.company
        so.blanket_order = bo_name
        so.delivery_date = nowdate()
        so.currency = getattr(bo, "currency", None) or \
                      frappe.get_value("Company", bo.company, "default_currency") or "USD"
        so.status = "Draft"

        for it in bo_items:
            item_doc = frappe.get_doc("Item", it.get("item_code"))

            warehouse = (
                it.get("warehouse") or
                frappe.get_value("Item Default", {"parent": it.get("item_code")}, "default_warehouse") or ""
            )
            bom_no = (
                it.get("bom_no") or
                frappe.get_value("BOM", {"item": it.get("item_code"), "is_default": 1}, "name")
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



# -------------------- Level 3: Sales Orders --------------------

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

    # -----------------------
    # FILTER: CUSTOMER
    # -----------------------
    if customer:
        sql += " AND so.customer = %s"
        params.append(customer)

    # -----------------------
    # FILTER: SEARCH TEXT (SO or Customer Name)
    # -----------------------
    if search_text:
        sql += " AND (so.name LIKE %s OR so.customer_name LIKE %s)"
        like = f"%{search_text}%"
        params.extend([like, like])

   
    date_filter = get_date_range(month, year)

    if date_filter:
        if date_filter["type"] in ("month_year", "year"):
            sql += " AND so.transaction_date BETWEEN %s AND %s"
            params.extend([date_filter["start"], date_filter["end"]])
            print(f"Filtering from {date_filter['start']} to {date_filter['end']}")
        elif date_filter["type"] == "month_only":
            sql += " AND MONTH(so.transaction_date) = %s"
            params.append(date_filter["month"])
            print(f"Filtering all years for month={date_filter['month']}")


    # -----------------------
    # LIMIT & ORDER
    # -----------------------
    sql += " ORDER BY so.transaction_date DESC LIMIT %s"
    params.append(limit)

    # Fetch orders
    orders = frappe.db.sql(sql, tuple(params), as_dict=True) or []
    result = []

    # -----------------------
    # FETCH ITEMS FOR EACH SO
    # -----------------------
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

@frappe.whitelist()
def get_boms_for_sales_orders(sales_orders: str | list = None):
    """
    Fetch Bill of Materials and related data (operations, moulds, item attributes)
    for items in selected Sales Orders. Optimized to reduce DB calls for Moulds.
    """
    if isinstance(sales_orders, str):
        try:
            # Assuming 'json' and other utilities are imported (e.g., from frappe.utils import flt)
            sales_orders = json.loads(sales_orders)
        except Exception:
            return []

    if not sales_orders:
        return []

    result = []
    mould_cache = {} # Cache for mould details to prevent redundant DB calls

    for so_name in sales_orders:
        try:
            # Assuming 'Document' and 'frappe' are correctly imported
            so: Document = frappe.get_doc("Sales Order", so_name)
        except frappe.DoesNotExistError:
            frappe.log_error(f"Sales Order not found: {so_name}", "get_boms_for_sales_orders")
            continue

        for so_item in so.items:
            item_code = so_item.item_code
            required_qty = flt(so_item.qty or 0)
            forced_bom = so_item.bom_no

            # 1. Fetch BOMs
            bom_filters = {"name": forced_bom} if forced_bom else {"item": item_code, "is_active": 1}
            boms = frappe.get_all(
                "BOM",
                filters=bom_filters,
                fields=["name as bom_no", "bom_type", "quantity as bom_qty"],
                limit_page_length=1 if forced_bom else 0
            ) or []

            # 2. Fetch Item fields (using get_value for simplicity, get_doc is fine too)
            item_data = frappe.db.get_value(
                "Item", item_code,
                ["pcs_wt", "runner_wt", "shot_wt", "gross_wt", "cycle_time", "cavity"], # Include cavity from item
                as_dict=True
            ) or {}
            
            # 3. Fetch Moulds linked to item (Optimized: get all mould numbers first)
            # FIX: Changed pluck=True to pluck="mould_no" to return a list of mould numbers.
            mould_nos = frappe.get_all(
                "Mould Selection",
                filters={"parent": item_code},
                fields=["mould_no"],
                order_by="idx",
                pluck="mould_no"
            )

            moulds = []
            if mould_nos:
                # Batch fetch mould details from the Mould DocType
                mould_details = frappe.get_all(
                    "Mould",
                    filters={"name": ["in", list(set(mould_nos))]}, # Use unique list of names
                    fields=["name as mould_no", "mould_name", "cavity_count"],
                    as_list=False
                )
                
                # Combine and format the details
                for d in mould_details:
                    # Cache the result for potentially large number of BOM lines
                    if d.mould_no not in mould_cache:
                        mould_cache[d.mould_no] = {
                            "mould_no": d.mould_no,
                            "mould_name": d.mould_name or "",
                            "cavity_count": int(flt(d.cavity_count or 0))
                        }
                
                # Use the ordered list of mould_nos to maintain UI order
                moulds = [mould_cache[mn] for mn in mould_nos if mn in mould_cache]


            # 4. Fetch BOM Items and Operations
            for bom in boms:
                bom_no = bom["bom_no"]
                
                # Fetch BOM Items
                bom_items = frappe.get_all(
                    "BOM Item",
                    filters={"parent": bom_no},
                    fields=["item_code as rm_item_code", "item_name", "stock_qty as qty_per_bom"],
                    order_by="idx"
                )

                # Fetch BOM Operations (Workstations)
                bom_operations = frappe.get_all(
                    "BOM Operation",
                    filters={"parent": bom_no},
                    fields=[
                        "operation", "workstation", "time_in_mins", "hour_rate",
                        "operating_cost", "batch_size", "cost_per_unit", "base_cost_per_unit"
                    ],
                    order_by="idx"
                )

                result.append({
                    "sales_order": so_name,
                    "customer": so.customer,
                    "item_code": item_code,
                    "bom_no": bom_no,
                    "bom_type": bom.get("bom_type") or "",
                    "bom_qty": flt(bom.get("bom_qty") or 0),
                    # Item fields
                    "cavity": int(flt(item_data.get("cavity") or 0)), # Cavity from Item Master
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


@frappe.whitelist()
def get_raw_materials_for_boms(boms: list = None):
    """
    Fetch raw material requirements aggregated across multiple BOMs, 
    including stock status and consumption data for production planning.
    
    FIX: Removed 'default_warehouse' from frappe.get_all to fix OperationalError (1054).
    """
    # Assuming json, frappe, flt, and _get_bin_totals are imported/defined elsewhere
    print("boms list in row material", boms)
    if not boms:
        return []

    # Convert JSON string to list if necessary
    if isinstance(boms, str):
        try:
            boms = json.loads(boms)
        except Exception:
            return []

    rm_totals = {}
    
    # --- 1. Aggregate required RM quantities across all BOMs ---
    for b in boms:
        if not isinstance(b, dict):
            continue 
            
        # Extract correct data from the frontend's BOM object
        bom_no = b.get("bom_no")
        req_qty = flt(b.get("required_for_selected_qty")) 
        
        if not bom_no or req_qty <= 0:
            continue

        # Get the base quantity the BOM is built for (safe float conversion)
        bom_qty = flt(frappe.db.get_value("BOM", bom_no, "quantity") or 1.0)

        # Fetch components for the BOM
        components = frappe.db.sql("""
            SELECT item_code, item_name, stock_qty AS qty, uom
            FROM `tabBOM Item` 
            WHERE parent=%s
        """, (bom_no,), as_dict=True) or []

        for comp in components:
            comp_item_code = comp["item_code"]
            
            # Calculate total required quantity for this RM
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

    # --- 2. Fetch Item Master and Stock Data in batches (Efficient batch fetching) ---
    rm_item_codes = list(rm_totals.keys())
    
    # FIX: 'default_warehouse' is REMOVED from the fields list to prevent the OperationalError (1054)
    item_master_data = frappe.get_all(
        "Item",
        filters={"name": ["in", rm_item_codes]},
        fields=["name", "stock_uom"],
    )
    item_data_map = {d.name: d for d in item_master_data}

    # Pre-fetch total consumption in one query
    consumed_data = frappe.db.sql("""
        SELECT sei.item_code, IFNULL(SUM(sei.qty),0) AS consumed_qty
        FROM `tabStock Entry Detail` sei
        JOIN `tabStock Entry` se ON se.name=sei.parent
        WHERE sei.item_code IN %(item_codes)s AND se.docstatus=1
          AND se.purpose IN ('Manufacture', 'Material Consumption for Manufacture')
        GROUP BY sei.item_code
    """, {"item_codes": rm_item_codes}, as_dict=True)

    consumed_map = {row["item_code"]: flt(row["consumed_qty"]) for row in consumed_data}

    # --- 3. Build Final Result ---
    result = []
    
    for rm_code, v in rm_totals.items():
        item_master = item_data_map.get(rm_code, {})
        # Assuming _get_bin_totals(rm_code) is a working function to get stock figures
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
            # Since it's not fetched, this defaults to ""
            "default_warehouse": item_master.get("default_warehouse") or "",
            "total_required_qty": required,
            "available_qty": available,
            "projected_qty": projected,
            "consumed_qty": consumed,
            "balance_qty": round(balance_qty, 6),
            "is_sufficient": is_sufficient
        })

    return result
# -------------------- Level 6: Work Orders for Blanket Orders --------------------
# File: aims_customization/api/mss_monthly_schedule.py

@frappe.whitelist()
def get_work_orders_for_so(so_list: str | list = None):
    """
    Fetch Work Orders for given Sales Orders.
    Returns a flat list of Work Order objects linked to the Sales Orders.
    
    FIX: Removed 'production_start_date' and 'production_end_date' to resolve OperationalError (1054).
    """
    # Assuming json, flt, and get_datetime are available from frappe.utils
    
    if not so_list:
        return []

    # Convert string input to list if needed
    if isinstance(so_list, str):
        try:
            so_list = json.loads(so_list)
        except Exception:
            so_list = [s.strip() for s in so_list.split(",") if s.strip()]

    if not so_list:
        return []

    # Prepare SQL placeholders
    placeholders = ",".join(["%s"] * len(so_list))

    # Query Work Orders (Removed production_start_date and production_end_date)
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
    
    # Helper to safely format dates, preventing crashes on None/Empty values
    def format_dt(dt):
        if dt:
            # Use frappe.utils.get_datetime to handle date/datetime conversion
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
            # Removed production_start_date and production_end_date here
            "expected_delivery_date": format_dt(wo.expected_delivery_date),
            "stock_uom": wo.stock_uom, 
        })
        
    return result


# -------------------- Level 7: Job Cards for Work Orders --------------------
@frappe.whitelist()
def get_job_cards_for_work_orders(wo_list: str | list = None):
    """
    Fetch Job Cards with associated RM consumption and stock for a list of Work Orders.
    """
    if not wo_list:
        return []

    # Normalize input
    if isinstance(wo_list, str):
        try:
            wo_list = json.loads(wo_list)
        except Exception:
            wo_list = [s.strip() for s in wo_list.split(",") if s.strip()]

    if not wo_list:
        return []

    placeholders = ",".join(["%s"] * len(wo_list))

    # Fetch job cards
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
        # Fetch RM items for each job card
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


# ---------------- LEVEL 8: Production / QC / Updates ----------------
@frappe.whitelist()
def get_capacity_plan(payload_json):
    payload = json.loads(payload_json) if isinstance(payload_json, str) else payload_json
    utilization = flt(payload.get("production_utilization") or 100)
    lines = payload.get("lines") or []

    result = []

    for ln in lines:
        item = ln.get("fg_item")
        qty = flt(ln.get("schedule_qty"))
        machine = ln.get("machine")
        month = ln.get("month")

        cycle_time, cavity = get_item_cycle_and_cavitys(item)
        per_piece_sec = cycle_time / max(cavity, 1)
        per_hour_qty = 3600 / per_piece_sec if per_piece_sec > 0 else 0

        required_hours = (qty * per_piece_sec) / 3600 if per_piece_sec else 0

        monthly_capacity = machine_monthly_capacity(
            machine,
            month,
            utilization
        )

        daily_shift_hours, working_days = get_machine_daily_info(machine, month)

        balance = monthly_capacity - required_hours

        result.append({
            "bom_no": ln.get("bom_no"),
            "fg_item": item,
            "machine": machine,
            "required_hours": round(required_hours, 2),
            "monthly_capacity_hours": monthly_capacity,
            "daily_capacity_hours": daily_shift_hours,
            "working_days": working_days,
            "machine_hourly_capacity": round(per_hour_qty, 2),
            "balance_hours": round(balance, 2),
            "overload_hours": round(abs(balance), 2) if balance < 0 else 0,
            "ok": balance >= 0
        })

    return result

def get_machine_daily_info(machine, month):
    ws = frappe.db.get_value(
        "Workstation",
        machine,
        ["holiday_list", "total_working_hours"],
        as_dict=True
    ) or {}

    shift_types = frappe.get_all("Shift Type", fields=["start_time", "end_time"])

    daily_hours = 0
    base = getdate()

    for s in shift_types:
        st = _to_time(s.start_time)
        et = _to_time(s.end_time)
        if not st or not et:
            continue

        start = datetime.combine(base, st)
        end = datetime.combine(base, et)
        if end <= start:
            end += timedelta(days=1)

        daily_hours += (end - start).total_seconds() / 3600

    if daily_hours <= 0:
        daily_hours = flt(ws.get("total_working_hours") or 8)

    working_days = get_working_days_in_current_month(
        ws.get("holiday_list"),
        month
    )

    return round(daily_hours, 2), working_days



@frappe.whitelist(allow_guest=True)
def create_work_orders(so_list):
    """Create Work Orders for selected Blanket Orders."""
    if isinstance(so_list, str):
        try:
            so_list = json.loads(so_list)
        except Exception:
            frappe.throw(_("Invalid Sales Order list"))

    if not isinstance(so_list, list) or not so_list:
        return {"status": "error", "message": "No Sales Orders provided"}

    created_wos = []

    for so_name in so_list:
        items = frappe.get_all(
            "Sales Order Item",
            filters={"parent": so_name},
            fields=["item_code", "qty", "warehouse", "bom_no"]
        )
        so_doc = frappe.get_doc("Sales Order", so_name)
        for item in items:
            wo = frappe.new_doc("Work Order")
            wo.production_item = item.item_code
            wo.qty = item.qty
            wo.sales_order = so_name
            wo.company = so_doc.company
            wo.bom_no = item.bom_no
            wo.fg_warehouse = item.warehouse
            wo.flags.ignore_mandatory = True
            wo.insert(ignore_permissions=True)
            created_wos.append(wo.name)

    return {"status": "success", "created_work_orders": created_wos}


# ---------------- Capacity Planning ----------------
@frappe.whitelist()
def get_workstations():
    workstations = frappe.get_all(
        "Workstation",
        fields=["name", "workstation_type", "total_working_hours", "holiday_list"],
        limit_page_length=1000
    )

    result = []
    for ws in workstations:
        shift_hours = flt(ws.total_working_hours or 8)
        working_days = get_working_days_in_current_month(ws.holiday_list)

        result.append({
            "name": ws.name,
            "machine_type": ws.workstation_type or "",
            "shift_hours": shift_hours,
            "working_days": working_days,
            "monthly_capacity_hours": shift_hours * working_days
        })

    return result


def get_working_days_in_current_month(holiday_list, month=None):
    """Return working days for a given YYYY-MM month using Holiday List."""
    if not month:
        today = date.today()
        year, month = today.year, today.month
    else:
        year, month = map(int, month.split("-"))

    _, total_days = calendar.monthrange(year, month)

    holidays = set()
    if holiday_list:
        holidays = {
            getdate(h.holiday_date)
            for h in frappe.get_all(
                "Holiday",
                filters={"parent": holiday_list},
                fields=["holiday_date"]
            )
        }

    working_days = 0
    for day in range(1, total_days + 1):
        d = date(year, month, day)
        if d.weekday() >= 5 or d in holidays:
            continue
        working_days += 1

    return working_days


def get_item_cycle_and_cavitys(item_code):
    """Fetch cycle time and cavity from Item custom fields."""
    row = frappe.db.get_value("Item", item_code, ["cycle_time", "cavity_coun"], as_dict=True) or {}
    return flt(row.get("cycle_time") or 0), int(flt(row.get("cavity_coun") or 1))


def _to_time(val):
    """
    Normalize Shift Type time fields.
    Supports datetime.time and datetime.timedelta
    """
    if isinstance(val, time):
        return val
    if isinstance(val, timedelta):
        total_seconds = int(val.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return time(hours % 24, minutes, seconds)
    return None
def get_machine_next_available_time(machine):
    """Return next available datetime for machine"""
    wos = frappe.get_all(
        "Work Order",
        filters={
            "workstation": machine,
            "status": ["in", ["Not Started", "In Process"]]
        },
        fields=["planned_end_date"],
        order_by="planned_end_date desc",
        limit=1
    )

    if wos:
        return get_datetime(wos[0].planned_end_date)

    return get_datetime()  # machine free now

def is_mould_available(mould, start, end):
    if not mould:
        return True

    clash = frappe.db.exists(
        "Work Order",
        {
            "custom_mould": mould,
            "planned_start_date": ["<", end],
            "planned_end_date": [">", start],
            "status": ["!=", "Completed"]
        }
    )
    return not clash

def split_qty_by_capacity(qty, per_hour_qty, shift_windows):
    """Split qty into chunks that fit shifts"""
    chunks = []

    for start, end in shift_windows:
        shift_hours = (end - start).total_seconds() / 3600
        max_qty = int(shift_hours * per_hour_qty)

        if qty <= 0:
            break

        used = min(qty, max_qty)
        chunks.append((used, shift_hours * (used / max_qty)))
        qty -= used

    return chunks


def machine_monthly_capacity(machine_name, month, utilization=100):
    """Calculate machine monthly capacity using Shift Types safely."""
    if not machine_name or not month:
        return 0

    ws = frappe.db.get_value(
        "Workstation",
        machine_name,
        ["holiday_list", "total_working_hours"],
        as_dict=True
    ) or {}

    shift_types = frappe.get_all(
        "Shift Type",
        fields=["start_time", "end_time"]
    )

    daily_shift_hours = 0
    base_date = getdate()

    for s in shift_types:
        start_t = _to_time(s.start_time)
        end_t = _to_time(s.end_time)

        if not start_t or not end_t:
            continue

        start = datetime.combine(base_date, start_t)
        end = datetime.combine(base_date, end_t)

        # Overnight shift
        if end <= start:
            end += timedelta(days=1)

        daily_shift_hours += (end - start).total_seconds() / 3600

    # Fallback if shifts not configured
    if daily_shift_hours <= 0:
        daily_shift_hours = flt(ws.get("total_working_hours") or 8)

    working_days = get_working_days_in_current_month(
        ws.get("holiday_list"),
        month
    )

    if working_days <= 0:
        return 0

    capacity = daily_shift_hours * working_days
    return round(capacity * (flt(utilization) / 100), 2)

@frappe.whitelist()
def validate_capacity(payload_json=None):
    payload = payload_json if isinstance(payload_json, dict) else json.loads(payload_json or "{}")
    lines = payload.get("lines") or []
    utilization = flt(payload.get("production_utilization") or 100)
    plan_start_date = payload.get("plan_start_date")
    plan_end_date = payload.get("plan_end_date")
    print("validate capacity lines:", lines)
    print("utilization:", utilization)
    result = []

    for ln in lines:
        item = ln.get("fg_item")
        qty = flt(ln.get("schedule_qty") or 0)
        machine = ln.get("machine")
        base_date = get_machine_next_available_time(machine)
        month = ln.get("month") or base_date.strftime("%Y-%m")
        cycle_time= flt(ln.get("cycle_time") or 0)
        cavity= int(flt(ln.get("cavity") or 1)) 

        if not item or not machine or qty <= 0 or not month:
            result.append({
                "fg_item": item,
                "bom_no": ln.get("bom_no"),
                "required_hours": 0,
                "machine_capacity_hours": 0,
                "ok": False,
                "message": _(f"Missing item {item}, machine {machine}, qty {qty} or month {month}")
            })
            continue

        
        per_piece_sec = cycle_time / max(cavity, 1)

        required_hours = (qty * per_piece_sec) / 3600 if per_piece_sec > 0 else 0
        capacity = machine_monthly_capacity(machine, month, utilization)

        ok = required_hours <= capacity

        result.append({
            "fg_item": item,
            "bom_no": ln.get("bom_no"),
            "required_hours": round(required_hours, 2),
            "machine_capacity_hours": round(capacity, 2),
            "ok": ok,
            "message": None if ok else _(
                "Required {0:.2f} hrs exceeds capacity {1:.2f} hrs"
            ).format(required_hours, capacity)
        })

    return result


@frappe.whitelist()
def create_mss_plan(payload_json):
    """Create Work Orders only (Sales Orders already exist)."""
    try:
        payload = json.loads(payload_json) if isinstance(payload_json, str) else payload_json
        lines = payload.get("lines") or []

        if not lines:
            frappe.throw(_("No lines provided"))

        # 1️⃣ Capacity validation
        validation = validate_capacity({
            "lines": lines,
            "production_utilization": payload.get("production_utilization", 100)
        })

        for v in validation:
            if not v.get("ok"):
                frappe.throw(
                    v.get("message")
                    or _("Capacity validation failed for BOM {0}").format(v.get("bom_no"))
                )

        created_work_orders = []

        # 2️⃣ Create Work Orders
        for ln in lines:
            sales_order = ln.get("sales_order")
            if not sales_order:
                frappe.throw(
                    _("Sales Order is required to create Work Orders for item: {0}")
                    .format(ln.get("fg_item"))
                )

            customer = resolve_customer(ln.get("related_bso"), ln)
            if not customer:
                frappe.throw(
                    _("Customer is mandatory for MSS line: {0}")
                    .format(ln.get("fg_item"))
                )

            wos = create_capacity_based_work_orders(ln, sales_order)
            created_work_orders.extend(wos)

        return {
            "success": True,
            "created_work_orders": created_work_orders
        }

    except Exception as e:
        frappe.log_error(message=str(e), title="create_mss_plan failed")
        frappe.throw(_("Error creating MSS Plan: ") + str(e))

def _get_customer_from_bso(bso_name):
    if not bso_name or bso_name == "UNASSIGNED":
        return None
    return frappe.db.get_value("Blanket Order", bso_name, "customer")

def resolve_customer(bso, line):
    """
    Resolve customer in safe priority order:
    1. Blanket Order
    2. MSS Line
    """
    # 1️⃣ From Blanket Order
    customer = _get_customer_from_bso(bso)
    if customer and frappe.db.exists("Customer", customer):
        return customer

    # 2️⃣ From MSS Line
    customer = line.get("customer")
    if customer and frappe.db.exists("Customer", customer):
        return customer

    return None

def calculate_start_end(start_dt, required_hours, shift_windows):
    remaining = required_hours
    current = start_dt

    for start, end in shift_windows:
        if current < start:
            current = start

        available = (end - current).total_seconds() / 3600
        if available <= 0:
            continue

        if remaining <= available:
            return current, current + timedelta(hours=remaining)

        remaining -= available
        current = end

    # Spill to next day
    return calculate_start_end(
        shift_windows[0][0] + timedelta(days=1),
        remaining,
        shift_windows
    )
    
def get_shift_windows(base_date):
    shifts = frappe.get_all(
        "Shift Type",
        fields=["start_time", "end_time"]
    )

    windows = []
    for s in shifts:
        start_t = _to_time(s.start_time)
        end_t = _to_time(s.end_time)

        if not start_t or not end_t:
            continue

        start = get_datetime(f"{base_date} {start_t}")
        end = get_datetime(f"{base_date} {end_t}")

        # Overnight shift
        if end <= start:
            end = end + timedelta(days=1)

        windows.append((start, end))

    return windows

def find_warehouse_like(company, pattern):
    return frappe.db.get_value(
        "Warehouse",
        {
            "company": company,
            "name": ["like", f"%{pattern}%"],
            "is_group": 0
        },
        "name"
    )
    
def resolve_warehouses(company, item_code, bom_no=None):

    # Item default
    item_wh = frappe.db.get_value(
        "Item Default",
        {"parent": item_code, "company": company},
        "default_warehouse"
    )

    mfg = frappe.db.get_value(
        "Manufacturing Settings",
        {"company": company},
        [
            "default_finished_goods_warehouse",
            "default_wip_warehouse"
        ],
        as_dict=True
    ) or {}

    fg = (
        item_wh
        or mfg.get("default_finished_goods_warehouse")
        or frappe.db.get_value(
            "Warehouse",
            {"company": company, "name": ["like", "%Finished%"], "is_group": 0},
            "name"
        )
    )

    wip = (
        mfg.get("default_wip_warehouse")
        or frappe.db.get_value(
            "Warehouse",
            {"company": company, "name": ["like", "%WIP%"], "is_group": 0},
            "name"
        )
    )

    if not fg or not wip:
        frappe.throw(_("FG or WIP Warehouse not configured"))

    return fg, wip


def create_capacity_based_work_orders(line, sales_order):
    fg_item = line["fg_item"]
    qty = flt(line["schedule_qty"])
    machine = line["machine"]
    bom_no = line["bom_no"]
    month = line["month"]

    so = frappe.get_doc("Sales Order", sales_order)
    company = so.company

    # 🔹 Resolve warehouses safely
    fg_warehouse, wip_warehouse = resolve_warehouses(
        company, fg_item, bom_no
    )

    cycle_time, cavity = get_item_cycle_and_cavitys(fg_item)
    per_piece_sec = cycle_time / max(cavity, 1)
    per_hour_qty = 3600 / per_piece_sec

    base_date = get_machine_next_available_time(machine)
    shift_windows = get_shift_windows(base_date.date())

    qty_chunks = split_qty_by_capacity(qty, per_hour_qty, shift_windows)
    
    
    created = []

    for chunk_qty, hours in qty_chunks:
        start_dt, end_dt = calculate_start_end(
            base_date,
            hours,
            shift_windows
        )

        if not is_mould_available(line.get("mould"), start_dt, end_dt):
            frappe.throw(_("Mould already in use during {0}").format(start_dt))

        wo = frappe.new_doc("Work Order")
        wo.company = company
        wo.production_item = fg_item
        wo.qty = chunk_qty
        wo.bom_no = bom_no
        wo.sales_order = sales_order
        bom = frappe.get_doc("BOM", bom_no)

        # 🔹 Copy Operations
        for op in bom.operations:
            wo.append("operations", {
                "operation": op.operation,
                "workstation": machine,
                "time_in_mins": op.time_in_mins or 1,
                "hour_rate": op.hour_rate,
                "batch_size": op.batch_size,
                "sequence_id": op.sequence_id,
                "description": op.description,
            })
        # wo.workstation = machine
        # wo.transfer_material_against = "Work Order"
        # ✅ MANDATORY FIELDS FIXED
        wo.fg_warehouse = fg_warehouse
        wo.wip_warehouse = wip_warehouse
        print("\n planned_start_date=", get_datetime(start_dt), "\nplanned_end_date=", end_dt)
        wo.planned_start_date = get_datetime(start_dt)
        wo.planned_end_date = get_datetime(end_dt)
        wo.expected_delivery_date = end_dt.date()
        wo.use_multi_level_bom = 1

        wo.flags.ignore_permissions = True
        wo.insert()
        # wo.submit()

        created.append(wo.name)
        base_date = end_dt

    return created


@frappe.whitelist()
def get_production_summary(customer=None, month=None, year=None):
    """
    Returns detailed production summary for a customer in a selected month/year.
    Includes: Blanket Orders, Sales Orders, Work Orders, BOMs, Stock, WIP, Dispatch.
    """

    if not customer or not month or not year:
        frappe.throw("Customer, month and year are required")

    # Parse month/year to date ranges
    from_date = get_first_day(f"{year}-{month}-01")
    to_date = get_last_day(f"{year}-{month}-01")

    # ---------------- Blanket Orders for customer ----------------
    bo_list = frappe.get_all(
        "Blanket Order",
        filters={"customer": customer, "transaction_date": ["between", [from_date, to_date]]},
        fields=["name", "transaction_date as order_date"]
    )

    if not bo_list:
        return []

    bo_names = [bo.name for bo in bo_list]

    # ---------------- Blanket Order Items ----------------
    bo_items = frappe.get_all(
        "Blanket Order Item",
        filters={"parent": ["in", bo_names]},
        fields=[
            "parent as bo_name", "item_code", "item_name", "qty as order_qty", "rate"
        ],
        order_by="parent, idx"
    )

    summary = []

    for item in bo_items:
        item_code = item.item_code
        bo_name = item.bo_name

        # Work Orders related to this BO and item
        wo_rows = frappe.db.sql(f"""
            SELECT
                production_item AS item_code,
                SUM(qty) AS total_qty,
                SUM(IFNULL(produced_qty,0)) AS produced_qty
            FROM `tabWork Order`
            WHERE sales_order=%s AND production_item=%s AND docstatus=1
            GROUP BY production_item
        """, (bo_name, item_code), as_dict=True)

        wo = wo_rows[0] if wo_rows else {"total_qty": 0, "produced_qty": 0}
        total_qty = wo.get("total_qty") or 0
        produced_qty = wo.get("produced_qty") or 0
        pending_qty = total_qty - produced_qty

        # Stock, WIP, Dispatch
        bin_tot = _get_bin_totals(item_code)
        dispatched = _get_dispatched_totals(bo_name, item_code)
        production = _get_production_totals(bo_name, item_code)
        material_transferred = production.get("material_transferred_for_manufacturing", 0)
        wip_qty = max(material_transferred - produced_qty, 0)
        balance_to_deliver_qty = total_qty - (dispatched.get("qty") or 0)

        # Item attributes
        item_attrs = frappe.db.get_value(
            "Item",
            item_code,
            ["cavity", "pcs_wt", "runner_wt", "shot_wt", "weight_per_unit", "cycle_time"],
            as_dict=True
        ) or {}

        # Remaining BO qty
        consumed_qty = _get_so_consumed_qty(bo_name, item_code)
        remaining_bo_qty = item.order_qty - consumed_qty

        summary.append({
            "customer": customer,
            "bo_name": bo_name,
            "order_date": frappe.utils.getdate(item.get("order_date")),
            "item_code": item_code,
            "item_name": item.item_name,
            "order_qty": item.order_qty,
            "schedule_qty": 0,
            "consumed_qty": consumed_qty,
            "rate": item.rate,

            # Production status
            "planned_qty": total_qty,
            "produced_qty": produced_qty,
            "pending_qty": pending_qty,
            "wip_qty": wip_qty,
            "available_stock": bin_tot.get("actual_qty", 0),
            "dispatched_qty": dispatched.get("qty", 0),
            "balance_to_deliver_qty": balance_to_deliver_qty,

            # Item attributes
            **item_attrs
        })

    return summary
