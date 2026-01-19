import frappe
import json
from aims_customization.api.mss_capacity_monthly import get_machine_capacity_monthly, get_item_capacity_monthly

def test_get_machine_capacity():
    print("Testing get_machine_capacity_monthly...")
    # Test without machines (should fetch all)
    res = get_machine_capacity_monthly(month="01", year="2026")
    if res.get("success"):
        data = res.get("data", [])
        print(f"  Success: Found {len(data)} machines.")
        if data:
            fields = data[0].keys()
            print(f"  Fields returned: {list(fields)}")
            required_fields = ["machine", "month_days", "daily_capacity_hrs", "shifts", "utilization", "month_capacity", "required_hours", "balance_hours", "required_shifts", "utilization_pct"]
            missing = [f for f in required_fields if f not in fields]
            if missing:
                print(f"  ERROR: Missing fields: {missing}")
            else:
                print("  All required fields present.")
    else:
        print(f"  FAILED: {res.get('message')}")

def test_get_item_capacity():
    print("\nTesting get_item_capacity_monthly...")
    # Test with some machines if possible, or just check fields
    res = get_item_capacity_monthly(month="01", year="2026")
    if res.get("success"):
        data = res.get("data", [])
        print(f"  Success: Found {len(data)} items.")
        if data:
            fields = data[0].keys()
            print(f"  Fields returned: {list(fields)}")
            required_fields = ["customer_name", "sales_order", "blanket_order", "item_code", "item_name", "work_order", "machine", "work_order_operation", "mould", "schedule_qty", "cavity", "cycle_time", "machine_hourly_capacity", "loading_hours", "month_days", "daily_capacity_hrs", "utilization", "wo_planned_date", "sales_order_date"]
            missing = [f for f in required_fields if f not in fields]
            if missing:
                print(f"  ERROR: Missing fields: {missing}")
            else:
                print("  All required fields present.")
                print(f"  Sample Item Data: {json.dumps(data[0], indent=2, default=str)}")
    else:
        print(f"  FAILED: {res.get('message')}")

if __name__ == "__main__":
    test_get_machine_capacity()
    test_get_item_capacity()
