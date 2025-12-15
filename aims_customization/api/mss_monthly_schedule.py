# aims_customization/api/mss_monthly_schedule.py
from __future__ import annotations
import json
from datetime import datetime, date, timedelta, time
import calendar
import frappe
from frappe.utils import nowdate, get_datetime, getdate, flt, time_diff_in_hours
from frappe import _
 
# -------------------- Helpers --------------------
def safe(val):
    return val if val not in (None, "") else ""

def _month_str_from_date(dt):
    if not dt:
        return ""
    if isinstance(dt, str):
        try:
            dt = datetime.strptime(dt, "%YYYY-%m-%d")
        except Exception:
            return ""
    return dt.strftime("%b-%Y")

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
def get_blanket_orders(search_text: str = None, customer: str = None, month: str = None, year: str = None, limit: int = 200):
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

    result = []
    for r in rows:
        bo_name = r["name"]

        # ---- 1️⃣ Total Blanket Order Qty ----
        total_bo_qty = frappe.db.sql("""
            SELECT SUM(qty) AS qty 
            FROM `tabBlanket Order Item`
            WHERE parent=%s
        """, (bo_name,), as_dict=True)[0].qty or 0

        # ---- 2️⃣ Total Qty Already Used in Sales Orders ----
        used_qty = frappe.db.sql("""
            SELECT SUM(soi.qty) AS qty
            FROM `tabSales Order Item` soi
            JOIN `tabSales Order` so ON so.name = soi.parent
            WHERE soi.blanket_order=%s 
              AND so.docstatus < 2
        """, (bo_name,), as_dict=True)[0].qty or 0

        # ---- 3️⃣ Remaining Qty ----
        remaining_qty = total_bo_qty - used_qty

        result.append({
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
            "tc_name": r["tc_name"],

            # ---- NEW FIELDS ----
            "total_blanket_qty": total_bo_qty,
            "remaining_qty": remaining_qty
        })

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
def get_sales_orders(search_text: str = None, month: str = None, customer: str = None, limit: int = 200 ):

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

   
    if month:
        try:
            if "-" in month and month.split("-")[1].isdigit() and len(month.split("-")[1]) == 2:
                # Format: Jan-25
                dt = datetime.strptime(month, "%b-%y")
            else:
                # Format: 2025-01
                dt = datetime.strptime(month, "%Y-%m")

            sql += " AND YEAR(so.transaction_date) = %s AND MONTH(so.transaction_date) = %s"
            params.extend([dt.year, dt.month])

        except Exception:
            pass

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
            "month": r["transaction_date"].strftime("%b-%Y"),
            "items": items,
        })

    return result


@frappe.whitelist()
def get_boms_for_sales_orders(sales_orders: str | list = None):
    """
    Fetch BOMs for items in multiple Sales Orders.
    Input: sales_orders = ["SO-0001", "SO-0002"]
    Output: BOM breakdown similar to your existing structure.
    """

    if not sales_orders:
        return []

    # Parse JSON input
    if isinstance(sales_orders, str):
        try:
            sales_orders = json.loads(sales_orders)
        except Exception as e:
            frappe.log_error(f"Failed to parse JSON: {e}", "get_boms_for_sales_orders")
            return []

    result = []

    for so_name in sales_orders:
        try:
            so = frappe.get_doc("Sales Order", so_name)
        except frappe.DoesNotExistError:
            frappe.log_error(f"Sales Order not found: {so_name}", "get_boms_for_sales_orders")
            continue

        for so_item in so.items:

            item_code = so_item.item_code
            required_qty = float(so_item.qty or 0)
            forced_bom = so_item.bom_no

            # Fetch BOMs
            boms = frappe.get_all(
                "BOM",
                filters={"name": forced_bom} if forced_bom else {"item": item_code},
                fields=["name as bom_no", "item", "quantity as bom_qty", "bom_type", "cavity", "pcs_wt", "runner_wt", "shot_wt", "gross_wt", "cycle_time","uom" ],
                limit_page_length=1 if forced_bom else None
            ) or []

            # if not boms:
            #     result.append({
            #         "sales_order": so_name,
            #         "item_code": item_code,
            #         "bom_no": "",
            #         "bom_qty": 0,
            #         "bom_type": "",
            #         "cavity" : "",
            #         "pcs_wt": 0,
            #         "runner_wt": 0, 
            #         "shot_wt": 0, 
            #         "gross_wt": 0, 
            #         "cycle_time": 0,
            #         "uom": "",
            #         "bom_items": [],
            #         "bom_operations": [],
            #         "moulds": [],
            #         "required_for_selected_qty": required_qty
            #     })
            #     continue

            # Fetch RM items for each BOM
            for bom in boms:
                bom_items = frappe.get_all(
                    "BOM Item",
                    filters={"parent": bom["bom_no"]},
                    fields=["item_code as rm_item_code", "item_name", "stock_qty as qty_per_bom"],
                    order_by="idx"
                )
                
               # Fetch BOM Operations (Workstations)
                bom_operations = frappe.get_all(
                    "BOM Operation",
                    filters={"parent": bom["bom_no"]},
                    fields=[
                        "operation",
                        "workstation",
                        "time_in_mins",
                        "hour_rate",
                        "operating_cost",
                        "batch_size",
                        "cost_per_unit",
                        "base_cost_per_unit"
                    ],
                    order_by="idx"
                )
                moulds = frappe.get_all(
                    "Mould Selection",
                    filters={"parent": item_code},
                    fields=["mould_no", "mould_name"],
                    order_by="idx"
                )
                result.append({
                    "sales_order": so_name,
                    "customer": so.customer,
                    "item_code": item_code,
                    "bom_no": bom.get("bom_no"),
                    "bom_qty": bom.get("bom_qty") or 0,
                    "bom_type": bom.get("bom_type"),
                    "cavity" : bom.get("cavity") or 0,
                    "pcs_wt": bom.get("pcs_wt") or 0,
                    "runner_wt": bom.get("runner_wt") or 0, 
                    "shot_wt": bom.get("shot_wt") or 0, 
                    "gross_wt": bom.get("gross_wt") or 0, 
                    "cycle_time": bom.get("cycle_time") or 0,
                    "uom": bom.get("uom") or "",
                    "bom_items": bom_items,
                    "bom_operations": bom_operations,
                    "moulds": moulds,
                    "required_for_selected_qty": required_qty or 0,
                })
                
    return result

@frappe.whitelist()
def get_raw_materials_for_boms(boms: list = None):
    if not boms:
        return []

    # Convert JSON string to list
    if isinstance(boms, str):
        try:
            boms = json.loads(boms)
        except Exception:
            return []

    rm_totals = {}

    for b in boms:
        # 🎯 FIX: b may be a string or a dict
        if isinstance(b, dict):
            bom_no = b.get("name")
            req_qty = float(b.get("required_for_selected_qty") or 0)
        else:
            bom_no = b       # string BOM name
            req_qty = 1      # default required qty (you can adjust as needed)

        if not bom_no:
            continue

        bom_qty = frappe.db.get_value("BOM", bom_no, "quantity") or 1.0

        components = frappe.db.sql("""
            SELECT item_code, item_name, stock_qty AS qty
            FROM `tabBOM Item` WHERE parent=%s
        """, (bom_no,), as_dict=True) or []

        for comp in components:
            comp_required = (req_qty / bom_qty) * (comp.get("qty") or 0.0)
            rm = comp["item_code"]

            if rm not in rm_totals:
                rm_totals[rm] = {
                    "rm_item_code": rm,
                    "rm_item_name": comp.get("item_name") or "",
                    "total_required_qty": 0.0
                }

            rm_totals[rm]["total_required_qty"] += comp_required

    # Build final structured response
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
            "bom_no" : bom_no,
            "rm_item_code": v["rm_item_code"],
            "rm_item_name": v["rm_item_name"],
            "total_required_qty": round(v["total_required_qty"], 6),
            "available_qty": bin_tot.get("actual_qty", 0),
            "consumed_qty": consumed
        })

    return result
# -------------------- Level 6: Work Orders for Blanket Orders --------------------
@frappe.whitelist()
def get_work_orders_for_so(so_list: str | list = None):
    """
    Fetch Work Orders for given Sales Orders.
    Returns a dictionary: { sales_order: [work_orders] }
    """
    result = {}

    if not so_list:
        return result

    # Convert string input to list if needed
    if isinstance(so_list, str):
        try:
            so_list = json.loads(so_list)
        except Exception:
            so_list = [s.strip() for s in so_list.split(",") if s.strip()]

    if not so_list:
        return result

    # Prepare SQL placeholders
    placeholders = ",".join(["%s"] * len(so_list))

    # Query Work Orders
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
        ORDER BY modified DESC
    """
    work_orders = frappe.db.sql(sql, tuple(so_list), as_dict=True) or []

    # Organize results by sales_order
    for wo in work_orders:
        so = wo.sales_order
        if so not in result:
            result = []
        result.append({
            "wo_name": wo.wo_name,
            "so_name": so,
            "production_item": wo.production_item,
            "wo_qty": wo.wo_qty,
            "produced_qty": wo.produced_qty,
            "status":wo.status,
            "material_transferred_for_manufacturing":wo.material_transferred_for_manufacturing,
            "disassembled_qty":wo.disassembled_qty,
            "bom_no":wo.bom_no,
            "company":wo.company,
            "fg_warehouse":wo.fg_warehouse,
            "scrap_warehouse":wo.scrap_warehouse,
            "wip_warehouse":wo.wip_warehouse,
            "planned_start_date":get_datetime(wo.planned_start_date).replace(microsecond=0).strftime("%Y-%m-%d %H:%M:%S"), 
            "planned_end_date":get_datetime(wo.planned_end_date).replace(microsecond=0).strftime("%Y-%m-%d %H:%M:%S"),
            "expected_delivery_date":get_datetime(wo.expected_delivery_date).replace(microsecond=0).strftime("%Y-%m-%d %H:%M:%S"),
            "stock_uom":wo.stock_uom, 
        })
        print("in python code ",result)
    return result


# -------------------- Level 7: Job Cards for Work Orders --------------------
@frappe.whitelist()
def get_job_cards_for_work_orders(wo_list: str | list = None):
    import json
    import frappe

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

    jcs = frappe.db.sql(
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

    for jc in jcs:
        jc_items = frappe.db.sql(
            """
            SELECT
                item_code,
                item_name,
                required_qty AS qty
            FROM `tabJob Card Item`
            WHERE parent=%s
            """,
            (jc["job_card"],),
            as_dict=True
        ) or []

        if jc_items:
            for ji in jc_items:
                consumed = _get_jobcard_consumed_for_wo(
                    jc["work_order"], ji["item_code"]
                )
                bin_tot = _get_bin_totals(ji["item_code"]) or {}

                result.append({
                    "job_card": jc["job_card"],
                    "job_card_status": jc["job_card_status"],
                    "operation": jc["operation"],
                    "workstation": jc["workstation"],
                    "rm_item_code": ji["item_code"],
                    "rm_item_name": ji["item_name"],
                    "required_qty": ji["qty"],
                    "available_qty": bin_tot.get("actual_qty", 0),
                    "consumed_qty": consumed,
                    "work_order": jc["work_order"],
                    "production_item": jc["production_item"],
                    "mould": jc["mould"],
                    "expected_start_date": jc["expected_start_date"],
                    "expected_end_date": jc["expected_end_date"],
                    "time_required": jc["time_required"],
                    "total_completed_qty": jc["total_completed_qty"],
                    "process_loss_qty": jc["process_loss_qty"],
                    "wip_warehouse": jc["wip_warehouse"],
                    "quality_inspection": jc["quality_inspection"],
                    "posting_date": jc["posting_date"],
                    "bom_no": jc["bom_no"]
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
                "consumed_qty": 0,
                "work_order": jc["work_order"],
                "production_item": jc["production_item"],
                "mould": jc["mould"],
                "expected_start_date": jc["expected_start_date"],
                "expected_end_date": jc["expected_end_date"],
                "time_required": jc["time_required"],
                "total_completed_qty": jc["total_completed_qty"],
                "process_loss_qty": jc["process_loss_qty"],
                "wip_warehouse": jc["wip_warehouse"],
                "quality_inspection": jc["quality_inspection"],
                "posting_date": jc["posting_date"],
                "bom_no": jc["bom_no"]
            })

    return result

# ---------------- LEVEL 8: Production / QC / Updates ----------------

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

    result = []

    for ln in lines:
        item = ln.get("fg_item")
        qty = flt(ln.get("schedule_qty") or 0)
        machine = ln.get("machine")
        month = ln.get("month")

        if not item or not machine or qty <= 0 or not month:
            result.append({
                "fg_item": item,
                "bom_no": ln.get("bom_no"),
                "required_hours": 0,
                "machine_capacity_hours": 0,
                "ok": False,
                "message": _("Missing item, machine, qty or month")
            })
            continue

        cycle_time, cavity = get_item_cycle_and_cavitys(item)
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
        start = datetime.combine(base_date, _to_time(s.start_time))
        end = datetime.combine(base_date, _to_time(s.end_time))
        if end <= start:
            end += timedelta(days=1)
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
    # ---------------- Item Default Warehouse ----------------
    item_default_wh = frappe.db.get_value(
        "Item Default",
        {
            "parent": item_code,
            "company": company
        },
        "default_warehouse"
    )

    # ---------------- Manufacturing Settings ----------------
    mfg_settings = frappe.db.get_value(
        "Manufacturing Settings",
        {"company": company},
        [
            "default_finished_goods_warehouse",
            "default_wip_warehouse",
            "default_scrap_warehouse",
        ],
        as_dict=True
    ) or {}

    # ---------------- FG Warehouse ----------------
    fg_warehouse = (
        item_default_wh
        or mfg_settings.get("default_finished_goods_warehouse")
        or find_warehouse_like(company, "Finished Goods")
    )

    if not fg_warehouse:
        frappe.throw(
            _("Finished Goods Warehouse not found for company {0}")
            .format(company)
        )

    # ---------------- WIP Warehouse ----------------
    wip_warehouse = (
        mfg_settings.get("default_wip_warehouse")
        or find_warehouse_like(company, "Work In Progress")
    )

    if not wip_warehouse:
        frappe.throw(
            _("WIP Warehouse not found for company {0}")
            .format(company)
        )

    return fg_warehouse, wip_warehouse

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
        wo.workstation = machine

        # ✅ MANDATORY FIELDS FIXED
        wo.fg_warehouse = fg_warehouse
        wo.wip_warehouse = wip_warehouse

        wo.planned_start_date = start_dt
        wo.planned_end_date = end_dt
        wo.expected_delivery_date = end_dt.date()
        wo.use_multi_level_bom = 1

        wo.flags.ignore_permissions = True
        wo.insert()
        wo.submit()

        created.append(wo.name)
        base_date = end_dt

    return created


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