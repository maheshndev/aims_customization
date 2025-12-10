# aims_customization/api/mss_monthly_schedule.py
from __future__ import annotations
import json
from datetime import datetime
import frappe
from frappe.utils import nowdate, get_datetime

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
        })
        
    return result

@frappe.whitelist(allow_guest=True)
def create_sales_order(items: str | list):

    if isinstance(items, str):
        items = json.loads(items)

    if not items:
        frappe.throw("No items provided.")

    # Group items by blanket_order
    orders = {}
    for it in items:
        bo_name = it.get("bo_name")
        if not bo_name:
            frappe.throw(f"Item {it.get('item_code')} is missing blanket_order")
        orders.setdefault(bo_name, []).append(it)

    created_sos = []
    skipped = []

    for bo_name, bo_items in orders.items():

        # 🔍 Check existing Sales Orders for this Blanket Order
        existing_so = frappe.get_all(
            "Sales Order",
            filters={"blanket_order": bo_name},
            fields=["name", "status"]
        )

        if existing_so:
            skipped.append({
                "blanket_order": bo_name,
                "existing_sales_orders": [so.name for so in existing_so]
            })
            continue  # Skip creating new SO

        # Fetch Blanket Order
        bo = frappe.get_doc("Blanket Order", bo_name)

        # Create new Sales Order
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
                "qty": it.get("order_qty"),
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
def get_sales_orders(search_text: str = None, month: str = None, customer: str = None, limit: int = 200):
    sql = """
        SELECT name, customer, customer_name, transaction_date, delivery_date, status, total_qty
        FROM `tabSales Order`
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
            "status": r["status"],
            "total_qty": r["total_qty"]
        } for r in rows
    ]

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

            if not boms:
                result.append({
                    "sales_order": so_name,
                    "item_code": item_code,
                    "bom_no": "",
                    "bom_qty": 0,
                    "bom_type": "",
                    "cavity" : "",
                    "pcs_wt": 0,
                    "runner_wt": 0, 
                    "shot_wt": 0, 
                    "gross_wt": 0, 
                    "cycle_time": 0,
                    "uom": "",
                    "bom_items": [],
                    "required_for_selected_qty": required_qty
                })
                continue

            # Fetch RM items for each BOM
            for bom in boms:
                bom_items = frappe.get_all(
                    "BOM Item",
                    filters={"parent": bom["bom_no"]},
                    fields=["item_code as rm_item_code", "item_name", "stock_qty as qty_per_bom"],
                    order_by="idx"
                )

                result.append({
                    "sales_order": so_name,
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
import json
import frappe

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
        WHERE sales_order IN ({placeholders}) AND docstatus = 1
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

    return result


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


@frappe.whitelist(allow_guest=True)
def create_work_orders(so_list):
    """
    Create Work Orders for selected Blanket Orders.
    """
    if isinstance(so_list, str):
        so_list = json.loads(so_list)

    created_wos = []

    for so_name in so_list:
        items = frappe.get_all("Sales Order Item", filters={"parent": so_name}, fields=["item_code", "qty", "warehouse", "bom_no"])
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
