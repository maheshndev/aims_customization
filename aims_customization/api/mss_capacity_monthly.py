# aims_customization/api/mss_capacity_monthly.py
import frappe
from frappe.utils import flt, cint, getdate, nowdate, get_last_day, get_first_day, add_days, time_diff_in_hours
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
        filters = {}
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
        
        month = cint(month) or getdate(nowdate()).month
        year = cint(year) or getdate(nowdate()).year
        
        first_day = get_first_day(f"{year}-{month:02d}-01")
        last_day = get_last_day(first_day)
        days_in_month = calendar.monthrange(year, month)[1]

        # User requirement: 2 shifts, each is 12 hours, total 24 hours daily.
        shifts = 2
        daily_capacity_hrs = 24.0
        utilization_val = flt(utilization)
        
        # Month Capacity = days * 24 * util%
        month_capacity = days_in_month * daily_capacity_hrs * (utilization_val / 100.0)

        # If machines is empty, fetch all non-group workstations
        if not machines:
            machines = frappe.get_all("Workstation", filters={}, pluck="name")

        result = []
        for m in machines:
            required_hours = _get_machine_usage_hours(m, first_day, last_day)
            balance_hours = month_capacity - required_hours
            
            # Required Shifts = required_hours / 12 (since each shift is 12 hours)
            required_shifts = round(required_hours / 12.0, 2)

            result.append({
                "machine": m,
                "month_days": days_in_month,
                "daily_capacity_hrs": daily_capacity_hrs,
                "shifts": shifts,
                "utilization": utilization_val,
                "month_capacity": round(month_capacity, 2),
                "required_hours": round(required_hours, 2),
                "balance_hours": round(balance_hours, 2),
                "required_shifts": required_shifts
            })
        
        return {"success": True, "data": result}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "MSS Capacity API: get_machine_capacity_monthly")
        return {"success": False, "message": f"Failed to load machine capacity: {str(e)}" }

def _get_machine_usage_hours(machine, start, end):
    # Calculate usage based on WO Start/End dates (Actual preferred over Planned)
    sql = """
        SELECT 
            wo.name,
            wo.planned_start_date,
            wo.planned_end_date,
            wo.actual_start_date,
            wo.actual_end_date
        FROM `tabWork Order` wo
        JOIN `tabWork Order Operation` wop ON wop.parent = wo.name
        WHERE wop.workstation = %s 
          AND (wo.planned_start_date BETWEEN %s AND %s)
          AND wo.docstatus != 2
        GROUP BY wo.name
    """
    rows = frappe.db.sql(sql, (machine, start, end), as_dict=True)
    
    total_hours = 0.0
    for r in rows:
        # Use Actual dates if available, else Planned
        s = r.actual_start_date if r.actual_start_date else r.planned_start_date
        e = r.actual_end_date if r.actual_end_date else r.planned_end_date
        
        if s and e:
            diff = time_diff_in_hours(e, s)
            if diff > 0:
                total_hours += diff

    return total_hours

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
        days_in_month = calendar.monthrange(year, month)[1]

        cond = ""
        params = {"start": first_day, "end": last_day}
        
        if customer:
            cond += " AND so.customer = %(customer)s"
            params["customer"] = customer
        
        if machines:
            cond += " AND wop.workstation IN %(machines)s"
            params["machines"] = tuple(machines)

        sql = f"""
            SELECT 
                so.customer_name,
                so.name as sales_order,
                (SELECT GROUP_CONCAT(DISTINCT sub_soi.blanket_order SEPARATOR ', ') FROM `tabSales Order Item` sub_soi WHERE sub_soi.parent = so.name AND sub_soi.blanket_order IS NOT NULL AND sub_soi.blanket_order != '') as blanket_order,
                item.name as item_code,
                item.item_name,
                wo.name as work_order,
                wop.workstation as machine,
                wop.operation as work_order_operation,
                wo.mould,
                (SELECT mould_name FROM `tabMould` WHERE name = wo.mould) as mould_name,
                wo.qty as schedule_qty,
                item.cavity,
                item.cycle_time,
                COALESCE(wo.actual_start_date, wo.planned_start_date) as wo_start_date,
                COALESCE(wo.actual_end_date, wo.planned_end_date) as wo_end_date,
                so.transaction_date as sales_order_date,
                wo.status
            FROM `tabWork Order` wo
            JOIN `tabWork Order Operation` wop ON wop.parent = wo.name
            JOIN `tabSales Order` so ON so.name = wo.sales_order
            JOIN `tabItem` item ON item.name = wo.production_item
            WHERE (COALESCE(wo.actual_start_date, wo.planned_start_date) <= %(end)s 
                   AND COALESCE(wo.actual_end_date, wo.planned_end_date) >= %(start)s)
              AND wo.docstatus != 2
              {cond}
            ORDER BY COALESCE(wo.actual_start_date, wo.planned_start_date) ASC
        """
        
        rows = frappe.db.sql(sql, params, as_dict=True)
        
        daily_capacity_hrs = 24.0
        
        result = []
        for r in rows:
            # machine_hourly_capacity = (3600 / cycle_time) * cavity if cycle_time else 0
            cycle_time = flt(r.cycle_time)
            cavity = flt(r.cavity) or 1.0
            
            machine_hourly_capacity = (3600.0 / cycle_time) * cavity if cycle_time > 0 else 0.0
            
            # loading_hours = schedule_qty / machine_hourly_capacity
            loading_hours = flt(r.schedule_qty) / machine_hourly_capacity if machine_hourly_capacity > 0 else 0.0

            result.append({
                "customer_name": r.customer_name,
                "sales_order": r.sales_order,
                "blanket_order": r.blanket_order or "",
                "item_code": r.item_code,
                "item_name": r.item_name,
                "work_order": r.work_order,
                "machine": r.machine,
                "work_order_operation": r.work_order_operation,
                "mould": r.mould,
                "mould_name": r.mould_name,
                "schedule_qty": flt(r.schedule_qty),
                "cavity": cavity,
                "cycle_time": cycle_time,
                "machine_hourly_capacity": round(machine_hourly_capacity, 2),
                "loading_hours": round(loading_hours, 2),
                "month_days": days_in_month,
                "daily_capacity_hrs": daily_capacity_hrs,
                "utilization": flt(utilization),
                "wo_planned_date": r.wo_start_date, # Template uses wo_planned_date
                "sales_order_date": r.sales_order_date
            })
            
        return {"success": True, "data": result}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "MSS Capacity API: get_item_capacity_monthly")
        return {"success": False, "message": f"Failed to load item capacity: {str(e)}" }

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
              AND wo.docstatus != 2
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
