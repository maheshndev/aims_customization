# MSS Dashboard (Monthly Schedule Screen)

The MSS Dashboard is the central hub for production planning. It provides a step-by-step workflow to convert customer demands into actionable production orders.

## Purpose

To provide a unified interface for planners to:

1.  Filter customer orders by month and year.
2.  Select specific Blanket Order line items.
3.  Review linked Sales Orders.
4.  Analyze BOM requirements and material availability.
5.  Plan machine capacity and generate Work Orders.
6.  Track Job Card progress.

## UI Components

The dashboard is built using a modular component architecture:

- **Filters**: Shared customer/date selector.
- **Section Cards**: Expandable sections for each workflow step.
- **Data Tables**: Interactive grids for Blanket Orders, Sales Orders, BOMs, RM, WOs, and Job Cards.
- **Capacity Planner**: A specialized component for machine load calculation.

## Backend APIs

The dashboard relies on the `mss_monthly_schedule.py` API module.

### Core Endpoints

#### `get_customers`

- **Description**: Fetches available customers for filtering.
- **Parameters**: `search_text` (optional), `customer_id` (optional).

#### `get_blanket_orders_with_items`

- **Description**: Retrieves selling blanket orders and their items based on filters.
- **Parameters**: `customer`, `month`, `year`.

#### `create_sales_order`

- **Description**: Creates new Sales Orders from selected Blanket Order items.
- **Parameters**: `items` (JSON list of items).

#### `get_sales_orders`

- **Description**: Lists Sales Orders filtered by date, customer, or linked blanket orders.

#### `get_boms_for_sales_orders`

- **Description**: Fetches standard or forced BOMs for the selected Sales Order items.
- **Includes**: Item details, mould selections, and operations.

#### `get_raw_materials_for_boms`

- **Description**: Calculates RM requirements vs current stock/bin availability for the selected BOMs.

---

[Return to Main README](../README.md)
