app_name = "aims_customization"
app_title = "Aims Customization"
app_publisher = "Assimilate Technologies"
app_description = "For aims common and core customozation"
app_email = "info@assimilatetechnologies.com"
app_license = "mit"



after_migrate = [
    "aims_customization.patches.v_0.make_lead_submittable.execute",
    "aims_customization.patches.v_0.add_pre_feasibility_link.execute",
    "aims_customization.patches.v_0.add_design_document_field_on_lead.execute",
    "aims_customization.patches.v_0.add_short_close_field_on_lead.execute",
    "aims_customization.patches.v_0.add_rejection_details_field_on_quotation.execute",
    "aims_customization.patches.v_0.add_field_customer_approval_email_on_quotation.execute",
    "aims_customization.patches.v_0.add_customer_po_attachment_field_on_sales_order.execute",
    "aims_customization.patches.v_0.add_short_close_reason_field.execute",
   
    "aims_customization.patches.v_0.add_rm_percentage_field_on_bom.execute",
    "aims_customization.patches.v_0.add_pre_feasibility_item_field_on_lead.execute",
    "aims_customization.patches.v_0.add_bom_type_field_on_bom.execute",
   
    "aims_customization.patches.v_0.change_the_datatype_qty_field_on_bomitem_from_float_to_data.execute",
    "aims_customization.patches.v_0.add_status_for_design_feasibility_on_quotation.execute",
   
    "aims_customization.patches.v_0.document_naming_series_for_shape.execute",
    "aims_customization.patches.v_0.add_design_document_attachment_on_quotation.execute",
    "aims_customization.patches.v_0.add_supplier_code_in_supplier_details.execute",
    "aims_customization.patches.v_0.add_mould_in_workorder.execute"

]
doctype_js = {
	"Lead": ["public/js/add_pre_feasibility_option_on_lead.js",
    "public/js/workflow_state_submitand_closed_hide_feasibility_button.js",
    "public/js/hide_workflow_action_closed_lead.js",
    "public/js/short_close_field_show_only_feasibility_reject.js"],
    "Pre Feasibility":["public/js/fetched_current_login_user_name_on_preparedby_field_on_pre_feasibility.js",
    "public/js/prefeasibility_template.js"],
    "Sales Order":"public/js/on_sales_order_hide_buttons_when_workflow_state_pending_for_approval.js",
    
    "BOM":"public/js/calculate_bom_quantity_based_on_gross_wt.js",
    "Sales Invoice": ["public/js/sales_invoice_and_credit_note_default_print_format_setting.js",
                      "public/js/default_value_for_declaration.js"],
    
}


doc_events = {
    "Lead": {
        "on_submit": "aims_customization.api.make_pre_feasibility_mandatory.before_submit_check_pre_feasibility",
        "on_update": "aims_customization.api.update_workflow_state_based_on_link_prefeasibility.before_save"
    },
    "Quotation": {
        "validate": "aims_customization.api.before_quote_reject_mandatory_rejection_detail.validate_quotation_workflow"
    },
    "Sales Order": {
        "validate": "aims_customization.api.short_close_reason_mandatory_when_sales_order_rejected.validate_rejection_details"
    }
}

# fixtures = [
#     "Workflow", "Workflow State", "Workflow Action",
#     {
#         "doctype": "Role",
#         "filters": [
#             ["role_name", "in", ["Design HOD", "Business HOD", "Marketing Manager/HOD", "Marketing Executive"]]
#         ]
#     },
    
#     {
#         "doctype": "Role Profile",
#         "filters": [
#             ["role_profile", "in", ["Design HOD", "Business HOD", "Marketing Manager/HOD", "Marketing Executive"]]
#         ]
#     },
#     {
#         "doctype": "Module Profile",
#         "filters": [
#             ["module_profile_name", "in", ["Design HOD", "Business HOD", "Marketing Manager/HOD", "Marketing Executive"]]
#         ]
#     }


# ]

fixtures = [
    {
        "doctype": "Workflow",
        "filters": [
            ["name", "in", [
                "Quotation Workflow",
                "Sales Order Workflow",
                "Lead Workflow",
                "Pre Feasibility Workflow"
            ]]
        ]
    },
    {
        "doctype": "Workflow State",
        
    },
    {
        "doctype": "Workflow Action Master",
        
    },
    {
        "doctype": "Role",
        "filters": [
            ["role_name", "in", [
                "Design HOD",
                "Business HOD",
                "Marketing Manager/HOD",
                "Marketing Executive"
            ]]
        ]
    },
    {
        "doctype": "Role Profile",
        "filters": [
            ["role_profile", "in", [
                "Design HOD",
                "Business HOD",
                "Marketing Manager/HOD",
                "Marketing Executive"
            ]]
        ]
    },
    {
        "doctype": "Module Profile",
        "filters": [
            ["module_profile_name", "in", [
                "Design HOD",
                "Business HOD",
                "Marketing Manager/HOD",
                "Marketing Executive"
            ]]
        ]
    }
]

