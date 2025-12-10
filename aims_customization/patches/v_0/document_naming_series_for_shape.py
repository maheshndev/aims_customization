import frappe

def execute():
    # If naming rule already exists, skip patch
    if frappe.db.exists("Document Naming Rule", {"document_type": "Shape"}):
        return

    # Create Naming Rule for Shape doctype
    rule = frappe.get_doc({
        "doctype": "Document Naming Rule",
        "document_type": "Shape",
        "priority": 0,
        "conditions": [],
        "prefix": "SH",
        "prefix_digits": 4,
        "counter": 0
        
    })

    rule.insert(ignore_permissions=True)
    frappe.db.commit()
