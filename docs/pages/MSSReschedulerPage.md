# Rescheduler Screen - Detailed Documentation

The Rescheduler Screen is a high-interactivity module for managing production timelines and resolving resource overlaps.

## 1. Functional Overview

Planners can visualize scheduled Work Orders on a timeline and drag them to new dates/times. The system performs real-time validation to ensure no two orders occupy the same mould or machine simultaneously.

## 2. API Specification (`mss_rescheduler_api.py`)

### `get_mss_schedule_range`

- **Purpose**: Data source for the timeline visualization.
- **Parameters**: `from_date`, `to_date`, `customer`, `sales_order`, `mould`, `item`, `shift`.
- **Query Filter**: Only fetches **Draft** Work Orders (`docstatus=0`).
- **Data Enrichment**: Automatically identifies the primary workstation from the first row of `tabWork Order Operation`.

### `mss_reschedule`

- **Purpose**: Core engine for date updates and conflict prevention.
- **Parameters**: `wo_name`, `planned_start_date`, `planned_end_date`.
- **Business Logic**:
  1.  **Naive Datetime Conversion**: Ensures timezone-agnostic comparisons.
  2.  **Holiday Validation**: Rejects changes if the new start or end falls on a holiday (as defined in `Company` -> `Default Holiday List`).
  3.  **Conflict Checks**:
      - **Mould Overlap**: Searches for any other non-cancelled WO using the same mould that overlaps with the new range.
      - **Workstation Overlap**: Searches for any other non-cancelled WO assigned to the same workstation that overlaps.
  4.  **Recalculation**: Maintains the original duration if only the start date is provided.
- **Returns**: `{"success": bool, "message": str}`.

### `mss_search_options`

- **Purpose**: Generic searchable selector for Customer, Sales Order, Item, Mould, and Shift Type.

### `get_holidays`

- **Purpose**: Fetches holiday dates for UI visualization (e.g., shading weekends/holidays on the Gantt chart).

## 3. Resource Conflict Logic

```sql
SELECT name FROM `tabWork Order`
WHERE name != %(name)s
  AND docstatus < 2
  AND mould = %(mould)s
  AND planned_start_date < %(end)s
  AND planned_end_date > %(start)s
```

_Note: Any overlap between the planned range [start, end] and any existing order range triggers a block._

---

[Return to Main README](../README.md)
