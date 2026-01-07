import frappe
from frappe.utils import get_datetime, add_to_date, time_diff_in_hours
from datetime import datetime

@frappe.whitelist(allow_guest=False)
def get_mss_schedule_range(from_date=None, to_date=None):
    if not from_date or not to_date:
        frappe.throw("from_date and to_date are required")

    # Ensure proper datetime format (naive)
    from_dt = get_datetime(from_date + " 00:00:00")
    to_dt = get_datetime(to_date + " 23:59:59")

    work_orders = frappe.db.sql("""
        SELECT
            wo.name AS wo_name,
            wo.production_item,
            wo.qty,
            wo.status,
            wo.mould,
            wo.planned_start_date,
            wo.planned_end_date,
            wo.sales_order
        FROM `tabWork Order` wo
        WHERE wo.status = 'Draft'
          AND wo.planned_start_date BETWEEN %s AND %s
        ORDER BY wo.planned_start_date
    """, (from_dt, to_dt), as_dict=True)

    for wo in work_orders:
        # Convert all datetimes to ISO strings for FullCalendar
        if wo.planned_start_date:
            wo["planned_start_date"] = wo.planned_start_date.isoformat()
        if wo.planned_end_date:
            wo["planned_end_date"] = wo.planned_end_date.isoformat()

        ops = frappe.get_all(
            "Work Order Operation",
            filters={"parent": wo.wo_name},
            fields=["workstation"]
        )
        wo["workstations"] = list(
            set(op.workstation for op in ops if op.workstation)
        )

    return work_orders

def make_naive(dt):
    """Convert aware datetime to naive in local timezone"""
    if dt.tzinfo:
        return dt.replace(tzinfo=None)
    return dt

@frappe.whitelist()
def mss_reschedule(wo_name, target_datetime):
    # Load main Work Order
    wo = frappe.get_doc("Work Order", wo_name)
    if wo.status != "Draft":
        frappe.throw("Only Draft Work Orders can be rescheduled")

    # Get first Shift Type
    shift_list = frappe.get_all("Shift Type", fields=["name", "start_time", "end_time"], limit=1)
    if not shift_list:
        frappe.throw("No Shift Type found")
    shift_doc = frappe.get_doc("Shift Type", shift_list[0].name)

    # Convert frontend ISO datetime to naive
    shift_start = make_naive(get_datetime(target_datetime))

    # Construct naive shift_end using same date + shift end_time
    shift_end = get_datetime(f"{shift_start.date()} {shift_doc.end_time}")
    shift_end = make_naive(shift_end)

    if shift_end <= shift_start:
        shift_end = add_to_date(shift_end, days=1)

    # Get workstation
    ops = frappe.get_all("Work Order Operation", filters={"parent": wo_name}, fields=["workstation"], limit=1)
    if not ops:
        frappe.throw("No workstation found")
    workstation = ops[0].workstation
    mould = wo.mould

    # Duration in hours
    duration = time_diff_in_hours(wo.planned_end_date, wo.planned_start_date)

    # Calculate new end datetime
    new_end = add_to_date(shift_start, hours=duration)
    if new_end > shift_end:
        frappe.throw("Work Order exceeds shift duration")

    # Find conflicts
    conflicts = frappe.db.sql("""
        SELECT DISTINCT wo.name
        FROM `tabWork Order` wo
        JOIN `tabWork Order Operation` op ON op.parent = wo.name
        WHERE wo.name != %s
          AND wo.status = 'Draft'
          AND (op.workstation = %s OR wo.mould = %s)
          AND wo.planned_start_date >= %s
        ORDER BY wo.planned_start_date
    """, (wo_name, workstation, mould, shift_start), as_dict=True)

    # Update main WO
    wo.planned_start_date = shift_start
    wo.planned_end_date = new_end
    wo.save(ignore_permissions=True)

    cursor = new_end
    updated_wos = [{
        "wo_name": wo.name,
        "planned_start_date": wo.planned_start_date.isoformat(),
        "planned_end_date": wo.planned_end_date.isoformat(),
        "workstations": [workstation],
        "mould": wo.mould
    }]

    # Update conflicts sequentially
    for row in conflicts:
        cwo = frappe.get_doc("Work Order", row.name)
        dur = time_diff_in_hours(cwo.planned_end_date, cwo.planned_start_date)
        end = add_to_date(cursor, hours=dur)
        if end > shift_end:
            break
        cwo.planned_start_date = cursor
        cwo.planned_end_date = end
        cwo.save(ignore_permissions=True)
        cursor = end

        updated_wos.append({
            "wo_name": cwo.name,
            "planned_start_date": cwo.planned_start_date.isoformat(),
            "planned_end_date": cwo.planned_end_date.isoformat(),
            "workstations": [workstation],
            "mould": cwo.mould
        })

    frappe.db.commit()
    return {"status": "success", "updated_wos": updated_wos}