
import frappe
from aims_customization.api.mss_capacity_monthly import get_machine_capacity_monthly, get_item_capacity_monthly
from frappe.utils import getdate, nowdate, add_days

def test_machine_capacity():
    print("\n--- Testing Machine Capacity ---")
    
    # Prerequisite: Create a dummy Work Order Operation for a machine if not exists
    # For now, let's just pick an existing machine or pass empty to get all
    
    # Test valid month/year
    res = get_machine_capacity_monthly(month=1, year=2026, machines=None, utilization=100)
    
    if not res.get("success"):
        print("FAILED: API call failed")
        return

    data = res.get("data", [])
    if not data:
        print("WARNING: No machine data returned (maybe no machines in system?)")
        return

    first_row = data[0]
    print(f"Sample Row: {first_row}")
    
    # Verify calculation logic: 24h * days * utilization
    expected_capacity = first_row['month_days'] * 24.0 * (first_row['utilization'] / 100.0)
    if abs(first_row['month_capacity'] - expected_capacity) > 0.1:
         print(f"FAILED: Calculation Mismatch! Expected {expected_capacity}, Got {first_row['month_capacity']}")
    else:
         print(f"PASSED: Capacity Calculation Correct ({expected_capacity})")

    # Verify shifts logic
    if first_row['shifts'] != 2:
        print(f"FAILED: Shifts should be 2, got {first_row['shifts']}")
    else:
        print("PASSED: Shifts verified as 2")

def test_item_capacity():
    print("\n--- Testing Item Capacity ---")
    
    # We need a work order to test this effectively. 
    # Just calling the API to ensure no SQL errors for now.
    res = get_item_capacity_monthly(month=1, year=2026, machines=None)
    
    if not res.get("success"):
        print("FAILED: Item API call failed")
        print(res.get("message"))
        return

    data = res.get("data", [])
    print(f"Items returned: {len(data)}")
    if data:
        print(f"Sample Item Row: {data[0]}")
        # Verify fields existence
        required_fields = ["item_code", "month_days", "daily_capacity_hrs", "loading_hours"]
        missing = [f for f in required_fields if f not in data[0]]
        if missing:
            print(f"FAILED: Missing fields in response: {missing}")
        else:
            print("PASSED: All required fields present in item response")

if __name__ == "__main__":
    try:
        frappe.connect("aims.local")
        test_machine_capacity()
        test_item_capacity()
    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        if frappe.db:
            frappe.db.close()
