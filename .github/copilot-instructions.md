# Copilot / AI Agent Instructions for aims_customization 🤖

Purpose
- Help an AI coding agent become productive immediately in this repository: what to change, how to run & test, and what patterns to follow.

Quick repo snapshot
- Frappe app (ERPNext/bench-style) with Python backend and a small Vue 3 + Vite frontend in `frontend/`.
- Key Python package: `aims_customization/aims_customization` (app code, hooks, APIs, patches, fixtures, public assets).

Big picture / architecture (why and where)
- This is a Frappe app that augments doctypes and workflows. Core pieces:
  - `hooks.py` — declares `after_migrate` patches, `doctype_js` mappings to `public/js/`, and `doc_events` that point to functions under `aims_customization/api/`.
  - `patches/v_0/` — small migration scripts that run from `after_migrate`. Changes here are applied on bench migrate.
  - `public/` — client JS and a bundled Vue app (`mss-vue-app`) that calls backend endpoints via `/api/method/aims_customization.api.<fn>`.
  - `fixtures/` — JSON fixtures (workflow, roles) that are installed with the app.

Essential developer workflows (how to run & test changes)
- Installing into a bench instance (most common path):
  - cd $PATH_TO_YOUR_BENCH
  - `bench get-app <repo_url> --branch <branch>`
  - `bench install-app aims_customization`
- Code formatting & pre-commit:
  - Run `pre-commit install` in `apps/aims_customization` (project uses `ruff`, `eslint`, `prettier`, `pyupgrade`).
  - Run linters locally or manually run `pre-commit run --all-files`.
- Frontend dev:
  - `cd frontend` then use `npm install` and `npm run dev` (Vite-based). The frontend bundles are placed under `aims_customization/public/mss-vue-app/`.
- Patches & migrations:
  - Add scripts into `patches/v_0/` and register them in `hooks.py` `after_migrate` list. Patches should be idempotent and safe to run multiple times.
- Where to test changes:
  - Backend Python changes can be tested by calling `frappe.get_doc` and invoking API endpoints or by running them in bench's worker environment. Frontend changes test via the browser and dev server.

Project-specific conventions & patterns
- API method naming and exposure:
  - Use `@frappe.whitelist()` to expose functions to the client (see `aims_customization/api/mss_monthly_schedule.py`). Frontend expects endpoints at `/api/method/aims_customization.api.<function>`.
- SQL usage and data access:
  - A lot of logic uses raw `frappe.db.sql` for optimized queries. Prefer efficient single queries over N queries when possible (see `get_blanket_orders` and related functions).
- Client JS mapping:
  - `doctype_js` in `hooks.py` wires doctype-specific client JS (file paths under `public/js`). Update there when adding UI behavior for doctypes.
- UI / bundle strategy:
  - A small SPA exists under `public/mss-vue-app` — it is built and bundled into the `public/` path and referenced by server-side pages.
- Patches naming & responsibilities:
  - Each file in `patches/v_0/` contains a function `execute` and is invoked on `after_migrate`. Use carefully for schema/data migrations.

Files & locations to reference when making changes
- Backend API & heavy logic: `aims_customization/api/*.py` (e.g., `mss_monthly_schedule.py`).
- Hooks & wiring: `aims_customization/hooks.py`.
- Frontend app: `frontend/` (source), `aims_customization/public/mss-vue-app/` (bundled output), `public/js/` (doctype scripts).
- Fixtures: `fixtures/` (module/role/workflow JSONs).
- Patches: `patches/v_0/` for migrations executed by `after_migrate`.
- Pre-commit & linting: `pyproject.toml`, `.eslintrc`, and pre-commit config implied in `README.md`.

Examples (copyable snippets)
- Expose Python function to frontend:

```python
# aims_customization/api/foo.py
import frappe

@frappe.whitelist()
def my_endpoint(arg=None):
    # return simple JSON-serializable object
    return {"ok": True, "arg": arg}
```
- Call from frontend (Axios):

```
axios.get('/api/method/aims_customization.api.mss_monthly_schedule.get_customers', { params: { search_text } })
```

Important checks and safety notes for PRs
- Ensure patch scripts in `patches/` are safe and idempotent — they run automatically on migration.
- When adding DB queries, prefer using parameterized queries and `as_dict=True`.
- Run `pre-commit` locally; the repo enforces formatting and lint rules.

What the AI should NOT do
- Do not assume a full test suite exists; do not merge breaking changes without verifying on a local bench instance.
- Avoid making irreversible database migrations without a clear rollback plan.

If anything is unclear or you'd like me to include additional patterns (e.g., common test steps, CI commands), tell me which area to expand and I'll iterate. ✅
