# Project Code Analysis Report

This report identifies unused code and summarizes the API structure within the `aims_customization` project.

## 1. Unused Code (Recommended for Removal)

The following components and files appear to be unused or are commented out in the current implementation.

### Frontend (Vue.js)

| File Path                                            | Status        | Reason                                                            |
| :--------------------------------------------------- | :------------ | :---------------------------------------------------------------- |
| `frontend/src/components/FinishGoodItems.vue`        | Unused        | No references found in the project.                               |
| `frontend/src/components/BOMComparisonModal.vue`     | Commented Out | Imported in `MSSDashboard.vue` but commented out in the template. |
| `frontend/src/components/BlanketOrders.vue`          | Commented Out | Imported in `MSSDashboard.vue` but commented out in the template. |
| `frontend/src/components/CapacityPlanner_snippet.js` | Unused        | Likely a temporary snippet or backup; no imports found.           |

> [!NOTE]
> In `frontend/src/pages/MSSDashboard.vue`, there are several blocks of commented-out template code (lines 10-12 and 43-44) and unused reactive state variables that could be cleaned up.

### Backend (Python/Frappe)

| File Path                                                                  | Status | Reason                                                              |
| :------------------------------------------------------------------------- | :----- | :------------------------------------------------------------------ |
| `aims_customization/api/backend_fix_snippet.py`                            | Unused | Isolated snippet file; not referenced in `hooks.py` or other files. |
| `aims_customization/patches/v_0/add_packing_details_tab_on_item.py`        | Unused | Not listed in `patches.txt` or `hooks.py`.                          |
| `aims_customization/patches/v_0/add_part_specification_tab_on_item.py`     | Unused | Not listed in `patches.txt` or `hooks.py`.                          |
| `aims_customization/patches/v_0/add_rework_and_checking_details.py`        | Unused | Not listed in `patches.txt` or `hooks.py`.                          |
| `aims_customization/patches/v_0/add_signature_field_on_pre_feasibility.py` | Unused | Not listed in `patches.txt` or `hooks.py`.                          |

> [!WARNING]
> The file `patches.txt` contains a reference to `aims_customization.patches.v_0.dia_field_mandatory_when_item_group_toolroolrm_round` (Line 15), but the corresponding file was not found in the directory.

---

## 2. API Code Summary

The project consists of a Vue.js frontend communicating with a Frappe (Python) backend via whitelisted methods.

### Backend Endpoints (Python)

Major logic is contained in the following modules:

1.  **MSS Monthly Schedule** (`aims_customization/api/mss_monthly_schedule.py`):
    - `get_customers`: Fetches customer list.
    - `get_blanket_orders`: Fetches blanket orders for filters.
    - `get_items_for_blanket_orders`: Fetches items for selected blanket orders.
    - `create_sales_order`: Generates Sales Orders from selection.
    - `get_sales_orders`: Fetches generated sales orders.
    - `get_boms_for_sales_orders`: Fetches BOMs and manufacturing details.
    - `get_production_control_dashboard`: Summary data for the dashboard.
2.  **Capacity Planning** (`aims_customization/api/mss_capacity_monthly.py`):
    - `get_machine_capacity_monthly`: Machine-level capacity data.
    - `get_item_capacity_monthly`: Item-level capacity calculations.
3.  **Rescheduler** (`aims_customization/api/mss_rescheduler_api.py`):
    - `get_mss_schedule_range`: Loads schedule data for rescheduling.
    - `mss_reschedule`: Performs the rescheduling logic.

### Frontend Service Mapping

The frontend organizes API calls into service files:

- **Main API Service** ([api.js](file:///frontend/src/services/api.js)): Maps to `mss_monthly_schedule.py`.
- **Capacity API Service** ([capavityApi.js](file:///frontend/src/services/capavityApi.js)): Maps to `mss_capacity_monthly.py`.
- **Rescheduler API Service** ([rescheduleApi.js](file:///frontend/src/services/rescheduleApi.js)): Maps to `mss_rescheduler_api.py`.

---

## 3. Recommended Next Steps

1.  **Verification**: Confirm that the features associated with "commented-out" components (like BOM Comparison) are indeed deprecated before deletion.
2.  **Cleanup**: Safely remove the identified unused files to reduce codebase bloat.
3.  **Patch Alignment**: Remove the dead reference in `patches.txt` to avoid potential migration warnings.
