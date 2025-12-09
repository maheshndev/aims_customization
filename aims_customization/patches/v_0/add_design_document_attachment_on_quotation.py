import frappe

def execute():
    field_name = "design_document_attachment"

    # Check if field already exists
    if not frappe.db.exists("Custom Field", {
        "dt": "Quotation",
        "fieldname": field_name
    }):

        frappe.get_doc({
            "doctype": "Custom Field",
            "dt": "Quotation",
            "label": "Design Document Attachment",
            "fieldname": field_name,
            "fieldtype": "Attach",
            "insert_after": "feasibility_status",
            "reqd": 0,
            "read_only": 0
        }).insert()

        frappe.db.commit()
