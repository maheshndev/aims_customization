import calendar
from datetime import time, timedelta, datetime
import frappe
from frappe.utils import getdate, nowdate, get_last_day, get_first_day
from frappe.utils.data import cint, flt


def get_month_days(month, year):
    if not month or not year:
        return 1
    return calendar.monthrange(int(year), int(month))[1]

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

def shift_hours_between(st, et):
    st = to_time(st)
    et = to_time(et)

    if not st or not et:
        return 0
    
    start = st.hour + st.minute / 60
    end = et.hour + et.minute / 60
    # Handle night shifts
    if end < start:
        end += 24

    return end - start

def get_shift_info():
    shifts = frappe.get_all("Shift Type", fields=["start_time", "end_time"])

    daily_hours = 0
    for s in shifts:
        daily_hours += shift_hours_between(s.start_time, s.end_time)
    return {"shift_count": len(shifts), "daily_hours": round(daily_hours, 2)}

def pcs_per_hour(cycle_time, cavity):

    return (3600 / max(1, flt(cycle_time))) * max(1, cint(cavity))

def to_time(val):
    """Convert Frappe Time (time or timedelta) to datetime.time"""
    if isinstance(val, time):
        return val
    if isinstance(val, timedelta):
        seconds = int(val.total_seconds())
        return time((seconds // 3600) % 24, (seconds % 3600) // 60, seconds % 60)
    return None

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
def get_machine_capacity_monthly( month: str = None, year: str = None, customer: str = None, utilization=90 ):
    today = getdate(nowdate())
    try:
        month = int(month) if month not in (None, "", 0) else today.month
        year = int(year) if year not in (None, "", 0) else today.year
    except Exception:
        frappe.throw("Invalid month or year")
        
    month_days = get_month_days(month, year)
    shift = get_shift_info()
    machines = frappe.get_all("Workstation", pluck="name")
    data = []

    for machine in machines:
        required_hrs = frappe.db.sql(
            """
            SELECT COALESCE(SUM(woo.time_in_mins), 0) / 60
            FROM `tabWork Order Operation` woo
            JOIN `tabWork Order` wo ON wo.name = woo.parent
            WHERE woo.workstation = %s
              AND MONTH(wo.planned_start_date) = %s
              AND YEAR(wo.planned_start_date) = %s
              AND (%s IS NULL OR %s = '' )
        """,
            (machine, month, year, customer, customer),
        )[0][0]

        month_capacity = shift["daily_hours"] * month_days * (flt(utilization) / 100)
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
            "required_shifts": (
                round(required_hrs / shift["daily_hours"], 2) if shift["daily_hours"] else 0
        ),})
    return data


@frappe.whitelist()
def get_item_capacity_monthly(month = None, year = None, customer = None, machines: list | str = None, utilization = 90):
    
    print("month: ", month, "year: ", year, "customer: ", customer, "machines: ", machines, "utilization", utilization )
    
    if isinstance(machines, str):
        machines = [machines]

    if not machines:
        return []

    month_days = get_month_days(month, year) if month and year else 0
    shift = get_shift_info()
    date_filter = get_date_range(month, year)

    conditions = []
    filters = {"machines": tuple(machines)}

    if month:
        conditions.append("MONTH(wo.planned_start_date) = %(month)s")
        filters["month"] = month

    if year:
        conditions.append("YEAR(wo.planned_start_date) = %(year)s")
        filters["year"] = year

    if customer:
        conditions.append("so.customer = %(customer)s")
        filters["customer"] = customer

    where_clause = " AND ".join(conditions)

    rows = frappe.db.sql(
        f"""
        SELECT
            so.customer_name,
            so.name AS sales_order,
            wo.production_item AS item_code,
            i.item_name,
            soi.qty AS schedule_qty,
            wo.mould,
            i.cavity,
            i.cycle_time,
            woo.workstation AS machine
        FROM `tabWork Order Operation` woo
        JOIN `tabWork Order` wo ON wo.name = woo.parent
        JOIN `tabItem` i ON i.name = wo.production_item
        JOIN `tabSales Order` so ON so.name = wo.sales_order
        JOIN `tabSales Order Item` soi
            ON soi.parent = so.name
            AND soi.item_code = wo.production_item
        WHERE woo.workstation IN %(machines)s
        {f"AND {where_clause}" if where_clause else ""}
        ORDER BY so.customer_name, so.name
        """,
        filters,
        as_dict=True,
    )

    result = []

    for r in rows:
        pcs_hr = pcs_per_hour(r.cycle_time, r.cavity)
        loading_hrs = (r.schedule_qty / pcs_hr) if pcs_hr else 0

        if month_days and shift.get("daily_hours"):
            utilization = (loading_hrs / (month_days * shift["daily_hours"])) * 100

        result.append({
            "customer_name": r.customer_name,
            "sales_order": r.sales_order,
            "item_code": r.item_code,
            "item_name": r.item_name,
            "schedule_qty": r.schedule_qty,
            "mould": r.mould,
            "cavity": r.cavity,
            "cycle_time": r.cycle_time,
            "machine": r.machine,
            "machine_hourly_capacity": round(pcs_hr, 2),
            "loading_hours": round(loading_hrs, 2),
            "month_days": month_days,
            "daily_capacity_hrs": shift.get("daily_hours", 0),
            "utilization": round(utilization, 2),
        })

    return result
