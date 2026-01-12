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
            wo.status,
            wo.mould,
            wo.sales_order,
            wo.planned_start_date,
            wo.planned_end_date,
            so.customer
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
    wo = frappe.get_doc("Work Order", wo_name)

    if wo.status != "Draft":
        frappe.throw("Only Draft Work Orders can be rescheduled")

    start = _naive(get_datetime(planned_start_date))
    end = _naive(get_datetime(planned_end_date))

    if end <= start:
        frappe.throw("Invalid time range")

    duration = time_diff_in_hours(end, start)

    # ---------------- HOLIDAY SKIP ----------------
    holiday_list = wo.get("holiday_list") or frappe.get_cached_value(
        "Company", wo.company, "default_holiday_list"
    )

    while is_holiday(start, holiday_list):
        start = add_to_date(start, days=1)

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

    # ---------------- SAVE MAIN WO ----------------
    wo.planned_start_date = start
    wo.planned_end_date = new_end
    wo.save(ignore_permissions=True)

    frappe.db.commit()
    return {"status": "success"}


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