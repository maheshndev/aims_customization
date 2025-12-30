import frappe
import calendar
from frappe.utils import nowdate, getdate
from frappe.utils.data import flt, cint

# ---------------------------------------------------------------------
# COMMON HELPERS
# ---------------------------------------------------------------------

def get_month_days(month, year):
    return calendar.monthrange(int(year), int(month))[1]

def shift_hours_between(st, et):
    start = st.hour + st.minute / 60
    end = et.hour + et.minute / 60
    if end < start:
        return (24 - start) + end
    return end - start

def get_shift_info():
    shifts = frappe.get_all(
        "Shift Type",
        fields=["start_time", "end_time"]
    )

    daily_hours = 0
    for s in shifts:
        daily_hours += shift_hours_between(s.start_time, s.end_time)

    return {
        "shift_count": len(shifts),
        "daily_hours": round(daily_hours, 2)
    }

def pcs_per_hour(cycle_time, cavity):
    return (3600 / max(1, flt(cycle_time))) * max(1, cint(cavity))


# ---------------------------------------------------------------------
# CUSTOMER SEARCH
# ---------------------------------------------------------------------

@frappe.whitelist()
def get_customer_list(search_text: str = None, customer_id: str = None, limit: int = 20):
    
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

@frappe.whitelist()
def get_machine_capacity_monthly(month=None, year=None, customer=None, utilization=90):

    today = getdate(nowdate())
    # ✅ SAFE parsing
    try:
        month = int(month) if month not in (None, "", 0) else today.month
        year = int(year) if year not in (None, "", 0) else today.year
    except Exception:
        frappe.throw("Invalid month or year")

    month_days = get_month_days(month, year)
    shift = get_shift_info()

    machines = frappe.get_all(
        "Workstation",
        filters={"disabled": 0},
        pluck="name"
    )

    data = []

    for machine in machines:
        required_hrs = frappe.db.sql("""
            SELECT COALESCE(SUM(woo.time_in_mins), 0) / 60
            FROM `tabWork Order Operation` woo
            JOIN `tabWork Order` wo ON wo.name = woo.parent
            WHERE woo.workstation = %s
              AND MONTH(wo.planned_start_date) = %s
              AND YEAR(wo.planned_start_date) = %s
              AND (%s IS NULL OR %s = '' OR wo.customer = %s)
        """, (machine, month, year, customer, customer, customer))[0][0]

        month_capacity = (
            shift["daily_hours"]
            * month_days
            * (flt(utilization) / 100)
        )

        balance = month_capacity - required_hrs

        data.append({
            "machine": machine,
            "month_days": month_days,
            "daily_capacity_hrs": shift["daily_hours"],
            "shifts": shift["shift_count"],
            "utilization": utilization,
            "month_capacity": round(month_capacity, 2),
            "required_hours": round(required_hrs, 2),
            "balance_hours": round(balance, 2),
            "required_shifts": round(
                required_hrs / shift["daily_hours"], 2
            ) if shift["daily_hours"] else 0
        })

    return data




# ---------------------------------------------------------------------
# ITEM CAPACITY (TABLE 2 – MACHINE WISE)
# ---------------------------------------------------------------------

@frappe.whitelist()
def get_item_capacity_monthly(month, year, customer=None, machines=None):
    """
    Fetch item capacity for selected machines in a given month/year
    """

    # normalize machines input
    if isinstance(machines, str):
        machines = [machines]

    if not machines:
        return []

    month_days = get_month_days(month, year)
    shift = get_shift_info()

    rows = frappe.db.sql("""
        SELECT
            so.customer_name,
            so.name AS sales_order,
            wo.production_item,
            i.item_name,
            soi.qty AS schedule_qty,
            wo.mould,
            i.cavity,
            i.cycle_time,
            woo.workstation
        FROM `tabWork Order Operation` woo
        JOIN `tabWork Order` wo ON wo.name = woo.parent
        JOIN `tabItem` i ON i.name = wo.production_item
        JOIN `tabSales Order` so ON so.name = wo.sales_order
        JOIN `tabSales Order Item` soi
             ON soi.parent = so.name
            AND soi.item_code = wo.production_item
        WHERE woo.workstation IN %(machines)s
          AND MONTH(wo.planned_start_date) = %(month)s
          AND YEAR(wo.planned_start_date) = %(year)s
          {customer_filter}
        ORDER BY so.customer_name, so.name
    """.format(
        customer_filter="AND wo.customer = %(customer)s" if customer else ""
    ), {
        "machines": tuple(machines),
        "month": month,
        "year": year,
        "customer": customer
    }, as_dict=True)

    result = []

    for r in rows:
        pcs_hr = pcs_per_hour(r.cycle_time, r.cavity)
        loading_hrs = r.schedule_qty / pcs_hr if pcs_hr else 0

        result.append({
            "customer": r.customer_name,
            "sales_order": r.sales_order,
            "item_code": r.production_item,
            "item_name": r.item_name,
            "schedule_qty": r.schedule_qty,
            "mould": r.mould,
            "cavity": r.cavity,
            "cycle_time": r.cycle_time,
            "machine": r.workstation,
            "machine_hourly_capacity": round(pcs_hr, 2),
            "loading_hours": round(loading_hrs, 2),
            "month_days": month_days,
            "daily_capacity_hrs": shift["daily_hours"],
            "utilization": 90
        })

    return result
