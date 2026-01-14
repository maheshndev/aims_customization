# aims_customization/api/mss_capacity_monthly.py
import frappe
from frappe.utils import flt, cint, getdate, nowdate, get_last_day, get_first_day, add_days
import json
from datetime import datetime, timedelta, time
import calendar

@frappe.whitelist()
def get_customer_list(search_text: str = None, customer_id: str = None, limit: int = 20):
    try:
        filters = {}
        if customer_id:
            filters["name"] = customer_id
        elif search_text:
            filters["customer_name"] = ["like", f"%{search_text}%"]
        
        rows = frappe.get_all(
            "Customer",
            filters=filters,
            fields=["name", "customer_name"],
            limit=limit
        )

        data = [{"name": r["name"], "customer_name": r["customer_name"]} for r in rows]
        return {"success": True, "data": data}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "MSS Capacity API: get_customer_list")
        return {"success": False, "message": "Failed to load customers"}

@frappe.whitelist()
def get_machine_list(search_text: str = None, workstation_id: str = None, limit: int = 20):
    try:
        filters = {"is_group": 0, "disabled": 0}
        if workstation_id:
            filters["name"] = workstation_id
        elif search_text:
            filters["name"] = ["like", f"%{search_text}%"]
        
        rows = frappe.get_all(
            "Workstation",
            filters=filters,
            fields=["name", "workstation_name"],
            limit=limit
        )

        data = [{"name": r["name"], "workstation_name": r["workstation_name"]} for r in rows]
        return {"success": True, "data": data}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "MSS Capacity API: get_machine_list")
        return {"success": False, "message": "Failed to load machines"}

@frappe.whitelist()
def get_machine_capacity_monthly(
    month=None,
    year=None,
    machines=None,
    utilization=100,
):
    try:
        if isinstance(machines, str):
            machines = json.loads(machines)
        
        if not machines:
            return {"success": True, "data": []}

        month = cint(month) or getdate(nowdate()).month
        year = cint(year) or getdate(nowdate()).year
        
        first_day = get_first_day(f"{year}-{month:02d}-01")
        last_day = get_last_day(first_day)
        days_in_month = (getdate(last_day) - getdate(first_day)).days + 1

        # Example logic: Total hours = 24 * days * utilization%
        # In a real app, you'd subtract holidays and shift non-working hours
        base_capacity = 24.0 * days_in_month * (flt(utilization) / 100.0)

        result = []
        for m in machines:
            usage = _get_machine_usage_hours(m, first_day, last_day)
            result.append({
                "machine": m,
                "total_capacity": base_capacity,
                "used_capacity": usage,
                "available_capacity": base_capacity - usage,
                "utilization_pct": round((usage / base_capacity * 100), 2) if base_capacity > 0 else 0
            })
        
        return {"success": True, "data": result}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "MSS Capacity API: get_machine_capacity_monthly")
        return {"success": False, "message": "Failed to load machine capacity"}

def _get_machine_usage_hours(machine, start, end):
    # Sum up planned/actual hours from Work Order operations in this period
    # Filter by workstation and date range
    sql = """
        SELECT SUM(time_required) 
        FROM `tabWork Order Operation` 
        WHERE workstation = %s 
          AND (planned_start_date BETWEEN %s AND %s)
          AND docstatus = 1
    """
    res = frappe.db.sql(sql, (machine, start, end))
    return flt(res[0][0]) / 60.0 if res and res[0][0] else 0.0

@frappe.whitelist()
def get_item_capacity_monthly(
    month=None,
    year=None,
    customer=None,
    machines=None,
    utilization=90,
):
    try:
        if isinstance(machines, str):
            machines = json.loads(machines)

        month = cint(month) or getdate(nowdate()).month
        year = cint(year) or getdate(nowdate()).year
        first_day = get_first_day(f"{year}-{month:02d}-01")
        last_day = get_last_day(first_day)

        cond = ""
        params = {"start": first_day, "end": last_day}
        
        if customer:
            cond += " AND so.customer = %(customer)s"
            params["customer"] = customer
        
        if machines:
            cond += " AND wo.workstation IN %(machines)s"
            params["machines"] = tuple(machines)

        sql = f"""
            SELECT 
                wo.production_item as item_code,
                item.item_name,
                so.customer,
                so.name as sales_order,
                (SELECT GROUP_CONCAT(DISTINCT sub_soi.blanket_order SEPARATOR ', ') FROM `tabSales Order Item` sub_soi WHERE sub_soi.parent = so.name AND sub_soi.blanket_order IS NOT NULL AND sub_soi.blanket_order != '') as blanket_order,
                SUM(wo.qty) as planned_qty,
                SUM(wo.produced_qty) as actual_qty,
                SUM(DATEDIFF(wo.planned_end_date, wo.planned_start_date) * 24) as req_hours
            FROM `tabWork Order` wo
            JOIN `tabSales Order` so ON so.name = wo.sales_order
            JOIN `tabItem` item ON item.name = wo.production_item
            WHERE wo.planned_start_date BETWEEN %(start)s AND %(end)s
              AND wo.docstatus = 1
              {cond}
            GROUP BY wo.production_item, so.customer, so.name
        """
        
        rows = frappe.db.sql(sql, params, as_dict=True)
        
        result = []
        for r in rows:
            result.append({
                "item_code": r.item_code,
                "item_name": r.item_name,
                "customer": r.customer,
                "sales_order": r.sales_order,
                "blanket_order": r.blanket_order or "",
                "planned_qty": flt(r.planned_qty),
                "actual_qty": flt(r.actual_qty),
                "required_hours": flt(r.req_hours),
                "progress": round((flt(r.actual_qty) / flt(r.planned_qty) * 100), 2) if flt(r.planned_qty) > 0 else 0
            })
            
        return {"success": True, "data": result}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "MSS Capacity API: get_item_capacity_monthly")
        return {"success": False, "message": "Failed to load item capacity"}

@frappe.whitelist()
def get_machine_workload_details(machine, start_date, end_date):
    try:
        # Returns list of Work Orders for a machine in a period
        sql = """
            SELECT 
                wo.name as work_order,
                wo.production_item as item_code,
                wo.qty,
                wo.planned_start_date,
                wo.planned_end_date,
                wo.status
            FROM `tabWork Order` wo
            WHERE wo.workstation = %s
              AND (wo.planned_start_date BETWEEN %s AND %s)
              AND wo.docstatus = 1
            ORDER BY wo.planned_start_date
        """
        rows = frappe.db.sql(sql, (machine, start_date, end_date), as_dict=True)
        return {"success": True, "data": rows}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "MSS Capacity API: get_machine_workload_details")
        return {"success": False, "message": "Failed to load workload details"}

def get_shift_details(workstation):
    # placeholder for actual shift logic from HR / Manufacturing
    return [
        {"name": "Day Shift", "start": "08:00:00", "end": "16:00:00"},
        {"name": "Evening Shift", "start": "16:00:00", "end": "00:00:00"}
    ]
