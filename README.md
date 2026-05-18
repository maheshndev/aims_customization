# Aims Customization

This Frappe app extends ERPNext functionalities with custom features. It includes:

- **Python Backend**: Augments doctypes and workflows with custom logic.
- **Vue.js Frontend**: A small Vue 3 + Vite application for interactive UIs.
- **API Exposure**: Seamless integration between frontend and backend.

### Installation

before install this app we required apps

1. [Frappe](https://github.com/frappe/frappe)
2. [ERPNext](https://github.com/frappe/erpnext)
3. [HRMS](https://github.com/frappe/hrms)
4. [Mould Management](https://github.com/assimilate-technologies/mold_management/)
5. [Material Weight Calculator](https://github.com/assimilate-technologies/material_weight_calculator)
6. [Gate Management](https://github.com/assimilate-technologies/gate_management)
7. [India Compliance](https://github.com/assimilate-technologies/india_compliance)

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
