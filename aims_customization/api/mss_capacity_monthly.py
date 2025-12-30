import frappe
from frappe import _
from frappe.utils import cint
import json
import calendar
from datetime import date
from frappe.utils import getdate, flt, cint

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


def get_month_days(month, year):
    return calendar.monthrange(int(year), int(month))[1]

def get_shift_hours():
    shifts = frappe.get_all(
        "Shift Type",
        fields=["start_time", "end_time"]
    )

    total_hours = 0
    for s in shifts:
        st = s.start_time
        et = s.end_time
        if et < st:
            total_hours += (24 - st.hour) + et.hour
        else:
            total_hours += (et.hour - st.hour)

    return {
        "shift_count": len(shifts),
        "daily_hours": total_hours
    }

def pcs_per_hour(cycle_time, cavity):
    return (3600 / flt(cycle_time)) * max(1, cint(cavity))


@frappe.whitelist()
def get_machine_capacity_monthly(month, year, customer, utilization=90):
    month_days = get_month_days(month, year)
    shift_info = get_shift_hours()

    machines = frappe.get_all(
        "Workstation",
        fields=["name"],
        filters={"disabled": 0}
    )

    data = []

    for m in machines:
        required_hrs = frappe.db.sql("""
            SELECT SUM(wo.qty / (
                (3600 / IFNULL(i.cycle_time,1)) * IFNULL(i.cavity,1)
            ))
            FROM `tabWork Order` wo
            JOIN `tabItem` i ON i.name = wo.production_item
            WHERE wo.workstation = %s
              AND MONTH(wo.planned_start_date) = %s
              AND YEAR(wo.planned_start_date) = %s
        """, (m.name, month, year))[0][0] or 0

        month_capacity = (
            shift_info["daily_hours"]
            * shift_info["shift_count"]
            * month_days
            * (flt(utilization) / 100)
        )

        balance = month_capacity - required_hrs

        data.append({
            "machine": m.name,
            "month_days": month_days,
            "daily_capacity_hrs": shift_info["daily_hours"],
            "shifts": shift_info["shift_count"],
            "utilization": utilization,
            "month_capacity": round(month_capacity, 2),
            "required_hours": round(required_hrs, 2),
            "balance_hours": round(balance, 2),
            "required_shifts": round(required_hrs / shift_info["daily_hours"], 2)
        })

    return data

@frappe.whitelist()
def get_item_capacity_monthly(month, year, customer):
    rows = frappe.db.sql("""
        SELECT
            so.customer_name,
            so.name AS sales_order,
            soi.item_code,
            soi.item_name,
            soi.qty AS schedule_qty,
            i.cycle_time,
            i.cavity,
            wo.workstation
        FROM `tabSales Order Item` soi
        JOIN `tabSales Order` so ON so.name = soi.parent
        LEFT JOIN `tabWork Order` wo ON wo.sales_order = so.name
        JOIN `tabItem` i ON i.name = soi.item_code
        WHERE MONTH(so.transaction_date) = %s
          AND YEAR(so.transaction_date) = %s
    """, (month, year), as_dict=True)

    result = []

    for r in rows:
        pcs_hr = pcs_per_hour(r.cycle_time, r.cavity)
        loading_hrs = r.schedule_qty / pcs_hr if pcs_hr else 0

        result.append({
            "customer": r.customer_name,
            "sales_order": r.sales_order,
            "item_code": r.item_code,
            "item_name": r.item_name,
            "schedule_qty": r.schedule_qty,
            "cavity": r.cavity,
            "cycle_time": r.cycle_time,
            "machine": r.workstation,
            "machine_hourly_capacity": round(pcs_hr, 2),
            "loading_hours": round(loading_hrs, 2)
        })

    return result
