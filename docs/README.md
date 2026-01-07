# AIMS Customization Module Documentation

This document provides comprehensive documentation for the `aims_customization` Frappe application, outlining its purpose, features, architecture, major modules like MSS, and essential developer workflows for both backend and frontend.

## Table of Contents
1. [Purpose](#1-purpose)
2. [Features](#2-features)
3. [Architecture Overview](#3-architecture-overview)
4. [Backend Development](#4-backend-development)
    * [API Endpoints](#41-api-endpoints)
    * [Doctypes](#42-doctypes)
    * [MSS Python APIs & Logic](#43-mss-python-apis--logic)
    * [Patches and Migrations](#44-patches-and-migrations)
    * [Fixtures](#45-fixtures)
    * [Hooks and Event Handling](#46-hooks-and-event-handling)
5. [MSS Tools](#5-mss-tools)
    * [What is MSS?](#51-what-is-mss)
    * [MSS Backend APIs](#52-mss-backend-apis)
    * [MSS Frontend (Vue SPA)](#53-mss-frontend-vue-spa)
6. [Frontend Development](#6-frontend-development)
    * [Structure and Technologies](#61-structure-and-technologies)
    * [API Interaction](#62-api-interaction)
7. [Developer Workflows](#7-developer-workflows)
    * [Backend Installation](#71-backend-installation)
    * [Frontend Setup & Usage](#72-frontend-setup--usage)
    * [Testing & Verification](#73-testing--verification)
8. [Project Conventions & Safety](#8-project-conventions--safety)
9. [Contribution & License](#9-contribution--license)

---

## 1. Purpose
The `aims_customization` module is a robust Frappe application designed to extend and augment doctypes and workflows in a Frappe/ERPNext system. Its primary objective is to deliver custom functionalities (such as MSS tools), business logic enhancements, migrations, and advanced UI frontends—increasing ERP capability without modifying core source code.

## 2. Features
- **MSS (Manufacturing Scheduling System) Tools:** Monthly scheduling, capacity sheets, rescheduling, etc.
- **Custom API Endpoints:** Add-on Python endpoints callable by frontend/UI or third-party tools.
- **Custom Doctypes:** Business-process data models such as Check Point List, Feasibility Check, Checklist Decision, Mould Selection, Density Table, Pre-feasibility, and items.
- **Workflow Enhancements:** Custom/extended flows for approval, rejections, and modular process states.
- **Data Patches & Migrations:** Scripts for schema/data upgrades via Frappe migration system.
- **Custom Print Formats:** Specialized printable layouts for document types (Quotation, Invoice, Notes).
- **Dedicated Frontend (Vue 3 SPA):** Fast and modern user tools for MSS and more, using a Vite+Vue+Tailwind stack.

## 3. Architecture Overview
- **Python Backend:** Core logic, business rules, custom endpoints—aligned with ERPNext/Frappe ORM and events.
- **Vue.js Frontend:** Component-based SPA app for advanced interfaces (e.g., MSS Scheduler, Capacity Sheet).
- **Frappe Hooks:** Wiring for events, patches, and UI integration.
- **Fixtures:** Role, workflow, and configuration data versioned as JSON.

```
aims_customization/
├── aims_customization/
│   ├── api/        # Python API business logic (incl. mss_monthly_schedule.py, etc.)
│   ├── doctype/    # Custom DocTypes for ERP
│   ├── page/       # Web pages (mss_rescheduler, mss_schedule_tool, etc.)
│   ├── print_format/
│   ├── report/
│   ├── hooks.py
│   ├── patches/
├── public/
│   └── mss-vue-app/   # Built Vue assets for MSS
├── frontend/
│   ├── src/           # Vue code & services
│   ├── package.json
│   └── ...
```

## 4. Backend Development

### 4.1. API Endpoints
Endpoints are defined under `aims_customization/aims_customization/api/` and exposed via the `@frappe.whitelist()` decorator. Example endpoint access pattern:
```python
@frappe.whitelist()
def my_api(data):
    return {'result': ...}
```
Call from API: `/api/method/aims_customization.api.module.method`.

### 4.2. Doctypes
DocTypes are custom data models for ERP documents, ledger entries, forms, etc., placed in `aims_customization/aims_customization/doctype/`. Examples include `check_point_list`, `feasibility_check`, `pre_feasibility`, etc.

### 4.3. MSS Python APIs & Logic
- Main files: `mss_monthly_schedule.py`, `mss_capacity_monthly.py`, `mss_rescheduler.py` in `api/`.
- These contain the backend logic for monthly scheduling, capacity calculation, rescheduling, and data feeds for frontend MSS apps.
- Use cases: Fetching customers, generating capacity reports, rescheduling entries, etc.

### 4.4. Patches and Migrations
- Located at `aims_customization/patches/v_0/` and registered in `hooks.py`.
- Patches must be idempotent—safe to run multiple times.
- Run on `bench migrate` or when installing app in new site.

### 4.5. Fixtures
- All workflow, role, and state configuration is kept in JSON fixtures under `aims_customization/fixtures/`.
- Includes: `role.json`, `workflow.json`, etc.

### 4.6. Hooks and Event Handling
- Central wiring via `hooks.py`.
    - `after_migrate` (patches), `doctype_js` (custom JS), `doc_events` (triggers on submit/cancel/update, etc.)

## 5. MSS Tools

### 5.1. What is MSS?
**MSS** (Manufacturing Scheduling System) provides advanced manufacturing planning and scheduling via custom Python APIs and a Vue.js-based Single Page Application. It is the main business extension in this module.

### 5.2. MSS Backend APIs
- Found in: `aims_customization/aims_customization/api/`:
    - `mss_monthly_schedule.py`  → Main API for MSS monthly/periodic schedule
    - `mss_capacity_monthly.py`  → Calculate and provide capacity data
    - `mss_rescheduler.py`      → Handle rescheduling tasks/requests
- Each API exposes methods (e.g. `get_customers`, `generate_capacity_sheet`, `reschedule_entry`) callable using `/api/method/aims_customization.api.mss_monthly_schedule.get_customers`.

### 5.3. MSS Frontend (Vue SPA)
- Source: All Vue SPA source is in `frontend/src/`.
- Entrypoints:
    - `mss-cp-main.js`     → Capacity Planning side
    - `mss-rescheduler-main.js` → Rescheduler UI
- Vue components and pages in `frontend/src/components/`, `frontend/src/pages/`.
- API interaction via Axios using endpoints above.
- Production build is output to: `aims_customization/public/mss-vue-app/`.

## 6. Frontend Development

### 6.1. Structure and Technologies
- **Vue 3** + **Vite** + **Tailwind CSS**.
- Service modules in `frontend/src/services/` handle API requests.
- Run locally for development; bundle for production.

### 6.2. API Interaction
- API requests by Axios. Example:
```javascript
axios.get('/api/method/aims_customization.api.mss_monthly_schedule.get_customers', { params: { search_text } })
```
- Handle backend authentication (generally via Frappe session or token environment).

## 7. Developer Workflows

### 7.1. Backend Installation
1. Add app to bench:
```bash
cd $PATH_TO_YOUR_BENCH
bench get-app <repo_url> --branch <branch>
bench install-app aims_customization
```
2. Apply patches:
```bash
bench migrate
```

### 7.2. Frontend Setup & Usage
1. Go to `frontend/`:
```bash
cd frontend
npm install
```
2. Start dev server:
```bash
npm run dev
```
3. Build for production:
```bash
npm run build
```
- Output goes to `aims_customization/public/mss-vue-app/` and referenced by Frappe UI.

### 7.3. Testing & Verification
- **Backend**: Test via direct API calls, Postman, or Frappe UI.
- **Frontend**: Test via browser on dev server, verify API connections.
- Always verify patches before migration on production. Review logs for errors.

## 8. Project Conventions & Safety
- All patches/scripts must be idempotent and safe for production.
- Follow Python and JS/TS (Vue) code guidelines enforced by `pre-commit`, `ruff`, and relevant linters.
- Do not include sensitive data in fixtures or commit history.
- Always test migrations, breaking changes, and new endpoints locally first.

## 9. Contribution & License
- Follow git branching and pull request best practices.
- All contributions require code review and testing.
- License is in `license.txt` at project root.
- For help, contact Assimilate Technologies <info@assimilatetechnologies.com>

---
For additional details on APIs, data models, or UI, see module-level docstrings and in-code comments. For frontend, read `frontend/README.md`, and for any issues, refer to `docs/` for extended guides.
