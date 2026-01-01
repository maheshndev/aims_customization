# AIMS Customization Module Documentation

This document provides detailed documentation for the `aims_customization` Frappe application, outlining its purpose, architecture, features, and developer workflows.

## Table of Contents
1.  [Purpose](#1-purpose)
2.  [Features](#2-features)
3.  [Architecture Overview](#3-architecture-overview)
4.  [Backend Development](#4-backend-development)
    *   [API Endpoints](#41-api-endpoints)
    *   [Doctypes](#42-doctypes)
    *   [Patches and Migrations](#43-patches-and-migrations)
    *   [Fixtures](#44-fixtures)
    *   [SQL Usage and Data Access](#45-sql-usage-and-data-access)
    *   [Hooks and Event Handling](#46-hooks-and-event-handling)
5.  [Frontend Development](#5-frontend-development)
    *   [Structure and Technologies](#51-structure-and-technologies)
    *   [API Interaction](#52-api-interaction)
6.  [Essential Developer Workflows](#6-essential-developer-workflows)
    *   [Installation](#61-installation)
    *   [Code Formatting & Pre-commit](#62-code-formatting--pre-commit)
    *   [Frontend Development Server](#63-frontend-development-server)
    *   [Testing Changes](#64-testing-changes)
7.  [Project-Specific Conventions & Patterns](#7-project-specific-conventions--patterns)
8.  [Important Checks and Safety Notes](#8-important-checks-and-safety-notes)
9.  [UI Components and Pages](#9-ui-components-and-pages)

---

## 1. Purpose
The `aims_customization` module is a Frappe application designed to extend and augment existing doctypes and workflows within an ERPNext/Frappe bench instance. Its primary purpose is to introduce custom functionalities, business logic, and user interfaces tailored to specific requirements, enhancing the core ERPNext system without directly modifying its source. This includes custom APIs, UI pages, data models (doctypes), and automated migration scripts (patches).

## 2. Features
The `aims_customization` module provides a range of features, including but not limited to:
*   **Custom API Endpoints**: Exposing Python functions as RESTful APIs for frontend and third-party integrations.
*   **Custom Doctypes**: Defining new data structures and extending existing ones for specialized business processes (e.g., Check Point List, Checklist Decision, Feasibility Check, Mould Selection, Density, Density Table, Pre-Feasibility, Pre-Feasibility Item).
*   **Workflow Enhancements**: Modifying and extending existing workflows (e.g., Pre-Feasibility, Sales Order rejection flows, Credit Note, Delivery Note, Payment Advice, Quotation, Sales Invoice).
*   **Custom Pages and UI**: Introducing new pages and interactive tools, such as the `MSS Schedule Tool` and `Monthly Capacity Sheet`.
*   **Print Formats**: Customizing print layouts for various documents like Quotations, Delivery Notes, Sales Invoices, Credit Notes, Delivery Challans, Payment Advice, and Pre-Feasibility reports.
*   **Data Migrations and Patches**: Automated scripts to manage database schema and data changes across different versions, including adding fields like BOM Type, Customer PO Attachment, Design Document Attachment, Customer Approval Email, Is Mold Item, Mould Detail Tab, Mould in Workorder, Mould Name, Moulds field, Other Than Mould/Moulding Item, and Packing Details Tab.

## 3. Architecture Overview
The `aims_customization` module operates as a standard Frappe application, integrating seamlessly with a Frappe/ERPNext bench instance. It leverages Frappe's architecture, which includes:
*   **Python Backend**: Frappe framework, database interactions (MariaDB/PostgreSQL), business logic, and API endpoints.
*   **Frontend**: A mix of Frappe's native Jinja2 templates and client-side JavaScript, augmented by a dedicated Vue 3 + Vite application for richer interactive experiences.
*   **Hooks**: `hooks.py` is central to wiring customizations, including `after_migrate` patches, `doctype_js` mappings, and `doc_events`.
*   **Fixtures**: JSON files for configuration and master data (e.g., workflows, roles).

The project structure reflects this architecture, with clear separation between backend Python code, frontend assets, and configuration files.

## 4. Backend Development
The backend is primarily written in Python and leverages the Frappe framework.

### 4.1. API Endpoints
API methods are defined under `aims_customization/api/` and exposed to the client using the `@frappe.whitelist()` decorator.
*   **Location**: `aims_customization/api/*.py`
*   **Naming Convention**: Frontend calls expect endpoints at `/api/method/aims_customization.api.<module>.<function>`.
*   **Examples**:
    *   `aims_customization.api.mss_monthly_schedule.py`
    *   `aims_customization.api.make_pre_feasibility_mandatory.py`

```python
# aims_customization/api/foo.py
import frappe

@frappe.whitelist()
def my_endpoint(arg=None):
    # return simple JSON-serializable object
    return {"ok": True, "arg": arg}
```

### 4.2. Doctypes
Custom Doctypes extend the data model of the Frappe application. These are defined under `aims_customization/aims_customization/doctype/`.
*   **Location**: `aims_customization/aims_customization/doctype/<doctype_name>/`
*   **Examples**: `check_point_list`, `checklist_decision`, `feasibility_check`, `mould_selection`, `pre_feasibility`, `density`, `density_table`, `pre_feasibility_item`.

### 4.3. Patches and Migrations
Patches are small Python scripts used for database schema changes or data migrations. They are executed automatically on `bench migrate`.
*   **Location**: `aims_customization/patches/v_0/`
*   **Registration**: Registered in `hooks.py` under the `after_migrate` list.
*   **Important**: Patches must be idempotent and safe to run multiple times.

### 4.4. Fixtures
Fixtures are JSON files used to install or update master data and configurations (e.g., roles, workflows) when the app is installed or updated.
*   **Location**: `aims_customization/fixtures/`
*   **Examples**: `module_profile.json`, `role.json`, `workflow.json`.

### 4.5. SQL Usage and Data Access
The module frequently uses raw `frappe.db.sql` for optimized database queries.
*   **Best Practice**: Prefer efficient single queries over N+1 queries. Use parameterized queries for security and `as_dict=True` for convenient data retrieval.
*   **Example**: See `get_blanket_orders` and related functions in API modules.

### 4.6. Hooks and Event Handling
`hooks.py` is the central configuration file for linking various customizations into the Frappe framework.
*   **Location**: `aims_customization/hooks.py`
*   **Key Sections**:
    *   `after_migrate`: Lists patch scripts to be executed after migration.
    *   `doctype_js`: Maps doctypes to client-side JavaScript files.
    *   `doc_events`: Triggers Python functions on specific document events (e.g., `on_update`, `on_submit`).

## 5. Frontend Development
The frontend components consist of client-side JavaScript for doctypes and a dedicated Vue 3 application.

### 5.1. Structure and Technologies
*   **Doctype-specific JS**: Files under `aims_customization/public/js/` provide UI behavior for specific Frappe doctypes, wired via `hooks.py`'s `doctype_js`.
*   **Vue SPA**: A more complex Single Page Application built with Vue 3 and Vite.
    *   **Source**: `frontend/`
    *   **Bundled Output**: `aims_customization/public/mss-vue-app/`
    *   **Technologies**: Vue 3, Vite, Tailwind CSS (via `postcss.config.js`, `tailwind.config.js`).

### 5.2. API Interaction
Frontend applications interact with the Frappe backend primarily through Axios, calling the whitelisted API methods.
*   **Example (Axios call from frontend)**:
    ```javascript
    axios.get('/api/method/aims_customization.api.mss_monthly_schedule.get_customers', { params: { search_text } })
    ```

## 6. Essential Developer Workflows

### 6.1. Installation
To install the `aims_customization` app into a Frappe bench instance:
```bash
# Navigate to your bench directory
cd $PATH_TO_YOUR_BENCH
bench get-app <repo_url> --branch <branch>
bench install-app aims_customization
```

### 6.2. Code Formatting & Pre-commit
The repository enforces code formatting and linting rules.
*   **Setup**: Run `pre-commit install` in `apps/aims_customization`.
*   **Tools**: `ruff` (Python), `eslint`, `prettier` (JavaScript/Vue), `pyupgrade`.
*   **Manual Run**: `pre-commit run --all-files`

### 6.3. Frontend Development Server
For developing the Vue.js application:
```bash
cd frontend
npm install
npm run dev
```
The bundled output will be placed in `aims_customization/public/mss-vue-app/`.

### 6.4. Testing Changes
*   **Backend Python**: Test by invoking API endpoints, running functions in the bench's worker environment, or using `frappe.get_doc`.
*   **Frontend**: Test via the browser, utilizing the dev server for the Vue app.

## 7. Project-Specific Conventions & Patterns
*   **API Method Naming**: `@frappe.whitelist()` to expose functions, with frontend calls targeting `/api/method/aims_customization.api.<function>`.
*   **SQL Usage**: Prioritize `frappe.db.sql` for performance with parameterized queries.
*   **Client JS Mapping**: `doctype_js` in `hooks.py` for connecting doctypes to client-side JavaScript.
*   **UI / Bundle Strategy**: Vue SPA built into `public/mss-vue-app` and referenced by server-side pages.
*   **Patches**: Idempotent `execute` functions in `patches/v_0/` for `after_migrate` operations.

## 8. Important Checks and Safety Notes
*   **Patches Idempotency**: Ensure all patch scripts in `patches/` are safe and idempotent, as they run automatically on migration.
*   **Database Queries**: Always use parameterized queries (`frappe.db.sql`) to prevent SQL injection vulnerabilities.
*   **Pre-commit**: Run `pre-commit` locally before pushing changes to ensure compliance with formatting and linting rules.
*   **Testing**: Do not assume a full test suite exists. Verify breaking changes on a local bench instance.
*   **Migrations**: Avoid irreversible database migrations without a clear rollback plan. 



