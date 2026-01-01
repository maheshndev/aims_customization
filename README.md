# Aims Customization

This Frappe app extends ERPNext functionalities with custom features. It includes:

*   **Python Backend**: Augments doctypes and workflows with custom logic.
*   **Vue.js Frontend**: A small Vue 3 + Vite application for interactive UIs.
*   **API Exposure**: Seamless integration between frontend and backend.

**Example: Exposing a Python function to the frontend**

```python
# filepath: aims_customization/api/foo.py
import frappe

@frappe.whitelist()
def my_endpoint(arg=None):
    return {"ok": True, "arg": arg}
```

### Installation

You can install this app using the [bench](https://github.com/frappe/bench) CLI:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app $URL_OF_THIS_REPO --branch develop
bench install-app aims_customization
```

### Contributing

This app uses `pre-commit` for code formatting and linting. Please [install pre-commit](https://pre-commit.com/#installation) and enable it for this repository:

```bash
cd apps/aims_customization
pre-commit install
```

Pre-commit is configured to use the following tools for checking and formatting your code:

- ruff
- eslint
- prettier
- pyupgrade

Project / File Structure Guidelines:
- Follow Frappe/ERPNext coding standards.

[filestructure.md](filestructure.md):


### License

mit


