# AIMS Customization Documentation

This project provides custom features for the AIMS (Advanced Inventory Management System) built on top of the Frappe framework. It focuses on production scheduling, capacity planning, and resourcing management.

## Project Overview

The `aims_customization` app introduces advanced tools for managing manufacturing cycles, blanket orders, and machine capacities. The primary objective is to streamline the transition from customer orders to production scheduling.

## Key Features

- **Monthly Schedule Screen (MSS) Dashboard**: A comprehensive tool to manage the flow from Blanket Orders to Job Cards.
- **Monthly Capacity Sheet**: Visualizes machine and item capacities to ensure optimal resource utilization.
- **Work Order Rescheduler**: An interactive interface for adjusting production schedules with real-time conflict detection.
- **BOM Comparison**: Tools to analyze and compare Bill of Materials for cost and efficiency.
- **Automated Validations**: Enhancements to standard Frappe doctypes like Quotations and Sales Orders for mandatory fields and workflow consistency.

## Technology Stack

- **Backend**: [Frappe Framework](https://frappeframework.com/) (Python)
- **Frontend**: [Vue.js 3](https://vuejs.org/) (integrated within Frappe pages)
- **Database**: MariaDB (standard Frappe DB)
- **Build Tool**: Vite (for the Vue.js frontend)

## Project Structure

```text
aims_customization/
├── aims_customization/      # Python Backend & Frappe Metadata
│   ├── api/                 # Custom Whitelisted APIs
│   ├── doctype/             # Custom Doctypes definitions
│   ├── page/                # Custom Frappe Pages (hosting Vue apps)
│   └── public/js/           # Frontend Client Scripts
├── frontend/                # Vue.js Frontend Source
│   ├── src/
│   │   ├── components/      # Reusable UI Components
│   │   ├── pages/           # Main Page Modules (Dashboard, Capacity, Rescheduler)
│   │   └── services/        # API Service layers
└── docs/                    # Integrated Documentation
```

## Core Workflow

1.  **Blanket Order Selection**: Filter and select open Blanket Order line items.
2.  **Sales Order Generation**: Generate Scheduled Sales Orders from selected items.
3.  **BOM Analysis**: Extract and analyze BOM items and operations.
4.  **Capacity Planning**: Check machine availability and raw material stock.
5.  **Work Order Creation**: Generate Work Orders based on capacity and material availability.
6.  **Progress Tracking**: Monitor Job Cards and production summary.

## Detailed Page Documentation

- [MSS Dashboard](pages/MSSDashboard.md)
- [Monthly Capacity Sheet](pages/MSSCapacityMonthlyPage.md)
- [Rescheduler Screen](pages/MSSReschedulerPage.md)

---

© 2026 AIMS Development Team
