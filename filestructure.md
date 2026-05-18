filestructure.md


## The following is the file / project structure of the `aims_customization` module:
<pre>
├── .git/
├── .github/
│   └── copilot-instructions.md
├── .gitignore
├── .pre-commit-config.yaml
├── .vscode/
├── README.md
├── aims_customization/
│   ├── .editorconfig
│   ├── .eslintrc
│   ├── __init__.py
│   ├── __pycache__/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── __pycache__/
│   │   ├── before_quote_reject_mandatory_rejection_detail.py
│   │   ├── make_pre_feasibility_mandatory.py
│   │   ├── mss_capacity_monthly.py
│   │   ├── mss_monthly_schedule.py
│   │   ├── short_close_reason_mandatory_when_sales_order_rejected.py
│   │   └── update_workflow_state_based_on_link_prefeasibility.py
│   ├── aims_customization/
│   │   ├── __init__.py
│   │   ├── __pycache__/
│   │   ├── doctype/
│   │   │   ├── __init__.py
│   │   │   ├── __pycache__/
│   │   │   ├── check_point_list/
│   │   │   ├── checklist_decision/
│   │   │   ├── checklist_template/
│   │   │   ├── density/
│   │   │   ├── density_table/
│   │   │   ├── feasibility_check/
│   │   │   ├── mould_selection/
│   │   │   ├── pre_feasibility/
│   │   │   ├── pre_feasibility_item/
│   │   │   └── ...
│   │   ├── page/
│   │   │   ├── __init__.py
│   │   │   ├── __pycache__/
│   │   │   ├── monthly_capacity_she/
│   │   │   └── mss_schedule_tool/
│   │   └── print_format/
│   │       ├── __init__.py
│   │       ├── credit_note_aims/
│   │       ├── delivery_note_challan/
│   │       ├── payment_advice_aims/
│   │       ├── pre_feasibility_aims/
│   │       ├── quotation_page_1_aims/
│   │       ├── quotation_page_2_aims/
│   │       └── sales_invoice_aims/
│   ├── config/
│   │   └── __init__.py
│   ├── fixtures/
│   │   ├── module_profile.json
│   │   ├── role_profile.json
│   │   ├── role.json
│   │   ├── workflow_action_master.json
│   │   ├── workflow_state.json
│   │   └── workflow.json
│   ├── hooks.py
│   ├── modules.txt
│   ├── patches/
│   │   ├── v_0/
│   │   │   ├── add_bom_type_field_on_bom.py
│   │   │   ├── add_customer_po_attachment_field_on_sales_order.py
│   │   │   ├── add_design_document_attachment_on_quotation.py
│   │   │   ├── add_design_document_field_on_lead.py
│   │   │   ├── add_field_customer_approval_email_on_quotation.py
│   │   │   ├── add_is_mold_item_field_on_item.py
│   │   │   ├── add_is_moulding_item_checkbox_on_item.py
│   │   │   ├── add_mould_detail_tab_on_item_master.py
│   │   │   ├── add_mould_in_workorder.py
│   │   │   ├── add_mould_name_field_on_item.py
│   │   │   ├── add_moulds_field_on_item.py
│   │   │   ├── add_other_than_mould_or_moulding_item.py
│   │   │   ├── add_packing_details_tab_on_item.py
│   │   │   └── ...
│   │   └── __init__.py
│   ├── patches.txt
│   ├── public/
│   │   ├── js/
│   │   │   └── ...
│   │   └── mss-vue-app/
│   │       └── ...
│   └── templates/
│       ├── __init__.py
│       └── pages/
│           └── ...
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── postcss.config.js
│   ├── public/
│   ├── README.md
│   ├── src/
│   │   ├── assets/
│   │   ├── components/
│   │   ├── main.js
│   │   ├── mss-cp-main.js
│   │   ├── mss-cp-style.css
│   │   ├── pages/
│   │   ├── services/
│   │   └── style.css
│   ├── tailwind.config.js
│   └── vite.config.js
├── license.txt
└── pyproject.toml
</pre>