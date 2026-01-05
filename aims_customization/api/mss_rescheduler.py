import frappe 
import json
from frappe.utils import get_datetime, flt

@frappe.whitelist()
def get_work_orders_for_so():
    
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
        ORDER BY planned_start_date DESC
    """
    work_orders = frappe.db.sql(sql, as_dict=True) or []

    result = []
    
    def format_dt(dt):
        if dt:
            return get_datetime(dt).replace(microsecond=0).strftime("%Y-%m-%d %H:%M:%S")
        return ""

    for wo in work_orders:
        
        result.append({
            "wo_name": wo.wo_name,
            "so_name": wo.sales_order,
            "production_item": wo.production_item,
            "wo_qty": flt(wo.wo_qty),
            "produced_qty": flt(wo.produced_qty), 
            "status": wo.status,
            "material_transferred_for_manufacturing": wo.material_transferred_for_manufacturing,
            "disassembled_qty": flt(wo.disassembled_qty),
            "bom_no": wo.bom_no,
            "company": wo.company,
            "fg_warehouse": wo.fg_warehouse,
            "scrap_warehouse": wo.scrap_warehouse,
            "wip_warehouse": wo.wip_warehouse,
            "planned_start_date": format_dt(wo.planned_start_date),
            "planned_end_date": format_dt(wo.planned_end_date),
            "expected_delivery_date": format_dt(wo.expected_delivery_date),
            "stock_uom": wo.stock_uom, 
        })
        
    return result
