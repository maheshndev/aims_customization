import frappe
from frappe.utils import add_to_date, get_datetime, time_diff_in_hours

def _naive(dt):
    return dt.replace(tzinfo=None) if dt.tzinfo else dt

def _make_naive(dt):
    return dt.replace(tzinfo=None) if dt.tzinfo else dt

def is_holiday(dt, holiday_list):
    if not holiday_list:
        return False
    return frappe.db.exists(
        "Holiday",
        {"holiday_date": dt.date(), "parent": holiday_list},
    )


@frappe.whitelist()
def get_mss_schedule_range(
    from_date, to_date, customer=None, sales_order=None, mould=None, item=None, shift=None
):
    from_dt = get_datetime(f"{from_date} 00:00:00")
    to_dt = get_datetime(f"{to_date} 23:59:59")

    conditions = ["(wo.planned_start_date <= %(to_dt)s AND wo.planned_end_date >= %(from_dt)s)"]

    values = {"from_dt": from_dt, "to_dt": to_dt}

    if customer:
        conditions.append("so.customer = %(customer)s")
        values["customer"] = customer
    if sales_order:
        conditions.append("wo.sales_order = %(sales_order)s")
        values["sales_order"] = sales_order
    if mould:
        conditions.append("wo.mould = %(mould)s")
        values["mould"] = mould
    if item:
        conditions.append("wo.production_item = %(item)s")
        values["item"] = item
    if shift:
        conditions.append("wo.shift = %(shift)s")
        values["shift"] = shift
    condition_sql = " AND ".join(conditions)

    return frappe.db.sql(
        f"""
        SELECT
            wo.name AS wo_name,
            wo.production_item,
            wo.item_name,
            wo.status,
            wo.mould,
            wo.sales_order,
            wo.planned_start_date,
            wo.planned_end_date,
            so.customer,
            (SELECT workstation FROM `tabWork Order Operation` WHERE parent = wo.name ORDER BY idx ASC LIMIT 1) as workstation
        FROM `tabWork Order` wo
        LEFT JOIN `tabSales Order` so ON so.name = wo.sales_order
        WHERE {condition_sql} AND wo.docstatus=0
        ORDER BY wo.planned_start_date
    """,
        values,
        as_dict=True,
    )


@frappe.whitelist()
def mss_reschedule(wo_name, planned_start_date, planned_end_date):
    import pytz # Import inside function to avoid top-level issues if any, or just strictly local usage
    wo = frappe.get_doc("Work Order", wo_name)

    if wo.status != "Draft":
        frappe.throw("Only Draft Work Orders can be rescheduled")

    start = _naive(get_datetime(planned_start_date))
    end = _naive(get_datetime(planned_end_date))

    if end <= start:
        frappe.throw("Invalid time range")

    duration = time_diff_in_hours(end, start)

    # ---------------- HOLIDAY VALIDATION (STRICT) ----------------
    holiday_list = wo.get("holiday_list") or frappe.get_cached_value(
        "Company", wo.company, "default_holiday_list"
    )

    if is_holiday(start, holiday_list):
        frappe.throw(f"Cannot schedule on Holiday: {start.date()}")
    
    if is_holiday(end, holiday_list):
        frappe.throw(f"Cannot schedule end time on Holiday: {end.date()}")

    # Calculate new end based on duration (simple add)
    # Note: If a job spans across a holiday, we might need more complex logic.
    # For now, strict check on Start/End points covers the request "dont allow... in weekend or holidays".
    new_end = add_to_date(start, hours=duration)

    # ---------------- WORKSTATION ----------------
    ops = frappe.get_all(
        "Work Order Operation",
        filters={"parent": wo.name},
        fields=["workstation"],
        order_by="idx asc",
        limit=1,
    )
    workstation = ops[0].workstation if ops else None

    # ---------------- CONFLICT CHECKS ----------------
    # Overlap Condition: (StartA < EndB) and (EndA > StartB)
    
    # 1. Mould Conflict
    if wo.mould:
        mould_conflict = frappe.db.sql("""
            SELECT name FROM `tabWork Order`
            WHERE name != %(name)s
            AND docstatus < 2
            AND mould = %(mould)s
            AND planned_start_date < %(end)s
            AND planned_end_date > %(start)s
            LIMIT 1
        """, {"name": wo.name, "mould": wo.mould, "start": start, "end": new_end})
        
        if mould_conflict:
            frappe.throw(f"Mould Conflict: Mould {wo.mould} is busy in Work Order {mould_conflict[0][0]}")

    # 2. Workstation Conflict
    if workstation:
        ws_conflict = frappe.db.sql("""
            SELECT wo.name 
            FROM `tabWork Order` wo
            JOIN `tabWork Order Operation` wop ON wop.parent = wo.name
            WHERE wo.name != %(name)s
            AND wo.docstatus < 2
            AND wop.workstation = %(workstation)s
            AND wo.planned_start_date < %(end)s
            AND wo.planned_end_date > %(start)s
            LIMIT 1
        """, {"name": wo.name, "workstation": workstation, "start": start, "end": new_end})
        
        if ws_conflict:
            frappe.throw(f"Workstation Conflict: Workstation {workstation} is busy in Work Order {ws_conflict[0][0]}")

    # ---------------- SAVE MAIN WO ----------------
    # Save naive datetime directly. 
    # Frontend sends Local Time string (e.g. "15:00"). 
    # We save "15:00" to DB so it matches visual time exactly.
    wo.planned_start_date = start
    wo.planned_end_date = new_end
    wo.save(ignore_permissions=True)

    frappe.db.commit()
    return {"status": "success"}


@frappe.whitelist()
def get_holidays(from_date, to_date, company=None):
    if not company:
        company = frappe.defaults.get_user_default("Company")
        
    holiday_list = frappe.get_cached_value("Company", company, "default_holiday_list")
    if not holiday_list:
        return []
        
    return frappe.db.sql("""
        SELECT holiday_date, description
        FROM `tabHoliday`
        WHERE parent = %(holiday_list)s
        AND holiday_date BETWEEN %(from_date)s AND %(to_date)s
    """, {"holiday_list": holiday_list, "from_date": from_date, "to_date": to_date}, as_dict=True)


@frappe.whitelist()
def mss_search_options(doctype, txt=None, limit=20):
    """
    Generic dropdown search API
    """
    if not doctype:
        frappe.throw("doctype is required")
    txt = f"%{txt}%" if txt else "%"

    allowed = {
        "Customer": ("name",),
        "Sales Order": ("name",),
        "Item": ("name", "item_name"),
        "Mould": ("name",),
        "Shift Type": ("name",),
    }

    if doctype not in allowed:
        frappe.throw("Invalid doctype")
    fields = allowed[doctype]
    conditions = " OR ".join([f"{f} LIKE %(txt)s" for f in fields])

    data = frappe.db.sql(
        f"""
        SELECT name
        FROM `tab{doctype}`
        WHERE ({conditions})
        ORDER BY modified DESC
        LIMIT %(limit)s
    """,
        {"txt": txt, "limit": limit},
        as_dict=True,
    )

    return [d.name for d in data]