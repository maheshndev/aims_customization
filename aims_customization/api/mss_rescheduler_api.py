import frappe
from frappe.utils import add_to_date, get_datetime, time_diff_in_hours

def _make_naive(dt):
    if not dt:
        return None
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
    try:
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
            # Shift filter will be applied in Python post-processing for time-based overlap
            pass
        
        condition_sql = " AND ".join(conditions)

        data = frappe.db.sql(
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
                wo.qty,
                (SELECT workstation FROM `tabWork Order Operation` WHERE parent = wo.name ORDER BY idx ASC LIMIT 1) as workstation
            FROM `tabWork Order` wo
            LEFT JOIN `tabSales Order` so ON so.name = wo.sales_order
            WHERE {condition_sql} AND wo.docstatus < 2
            ORDER BY wo.planned_start_date
        """,
            values,
            as_dict=True,
        )
        if shift:
            from datetime import datetime, timedelta
            shift_doc = frappe.get_doc("Shift Type", shift)
            s_start_time = shift_doc.start_time
            s_end_time = shift_doc.end_time
            
            filtered_data = []
            for wo in data:
                wo_start = wo.planned_start_date
                wo_end = wo.planned_end_date
                
                if not wo_start or not wo_end:
                    continue
                    
                # Check overlap for each day the WO spans
                overlap = False
                curr_day = wo_start.date()
                while curr_day <= wo_end.date():
                    # Defensive check for timedelta vs time
                    s_t_start = (datetime.min + s_start_time).time() if isinstance(s_start_time, timedelta) else s_start_time
                    s_t_end = (datetime.min + s_end_time).time() if isinstance(s_end_time, timedelta) else s_end_time
                    
                    s_dt_start = datetime.combine(curr_day, s_t_start)
                    if s_t_end < s_t_start:
                        s_dt_end = datetime.combine(curr_day + timedelta(days=1), s_t_end)
                    else:
                        s_dt_end = datetime.combine(curr_day, s_t_end)
                    
                    if max(wo_start, s_dt_start) <= min(wo_end, s_dt_end):
                        overlap = True
                        break
                    curr_day += timedelta(days=1)
                
                if overlap:
                    filtered_data.append(wo)
            data = filtered_data

        return {"success": True, "data": data}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "MSS Rescheduler API: get_mss_schedule_range")
        return {"success": False, "message": f"Failed to load schedule range: {str(e)}"}


@frappe.whitelist()
def mss_reschedule(wo_name, planned_start_date, planned_end_date):
    try:
        wo = frappe.get_doc("Work Order", wo_name)

        if wo.status != "Draft":
            return {"success": False, "message": "Only Draft Work Orders can be rescheduled"}

        start = _make_naive(get_datetime(planned_start_date))
        end = _make_naive(get_datetime(planned_end_date))

        if end <= start:
            return {"success": False, "message": "Invalid time range"}

        duration = time_diff_in_hours(end, start)

        holiday_list = wo.get("holiday_list") or frappe.get_cached_value(
            "Company", wo.company, "default_holiday_list"
        )

        if is_holiday(start, holiday_list):
            return {"success": False, "message": f"Cannot schedule on Holiday: {start.date()}"}
        
        if is_holiday(end, holiday_list):
            return {"success": False, "message": f"Cannot schedule end time on Holiday: {end.date()}"}

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
                return {"success": False, "message": f"Mould Conflict: Mould {wo.mould} is busy in Work Order {mould_conflict[0][0]}"}

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
                return {"success": False, "message": f"Workstation Conflict: Workstation {workstation} is busy in Work Order {ws_conflict[0][0]}"}

        wo.planned_start_date = start
        wo.planned_end_date = new_end
        wo.save(ignore_permissions=True)

        frappe.db.commit()
        return {"success": True, "message": f"Work Order {wo.name} rescheduled successfully"}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "MSS Rescheduler API: mss_reschedule")
        return {"success": False, "message": f"Reschedule failed: {str(e)}"}


@frappe.whitelist()
def get_holidays(from_date, to_date, company=None):
    try:
        if not company:
            company = frappe.defaults.get_user_default("Company")
            
        holiday_list = frappe.get_cached_value("Company", company, "default_holiday_list")
        if not holiday_list:
            return {"success": True, "data": []}
            
        data = frappe.db.sql("""
            SELECT holiday_date, description
            FROM `tabHoliday`
            WHERE parent = %(holiday_list)s
            AND holiday_date BETWEEN %(from_date)s AND %(to_date)s
        """, {"holiday_list": holiday_list, "from_date": from_date, "to_date": to_date}, as_dict=True)
        
        return {"success": True, "data": data}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "MSS Rescheduler API: get_holidays")
        return {"success": False, "message": "Failed to load holidays"}


@frappe.whitelist()
def mss_search_options(doctype, txt=None, limit=20):
    try:
        if not doctype:
            return {"success": False, "message": "doctype is required"}
            
        txt = f"%{txt}%" if txt else "%"

        allowed = {
            "Customer": ("name", "customer_name"),
            "Sales Order": ("name", "customer_name"),
            "Item": ("name", "item_name"),
            "Mould": ("name", "mould_name"),
            "Shift Type": ("name",),
        }

        if doctype not in allowed:
            return {"success": False, "message": f"Invalid doctype: {doctype}"}
            
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

        return {"success": True, "data": [d.name for d in data]}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "MSS Rescheduler API: mss_search_options")
        return {"success": False, "message": str(e)}