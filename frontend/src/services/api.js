import axios from "axios";

export const api = {
	// -------------------- Level 1 --------------------
	// In your API service file (e.g., api.js)

	getCustomers: (search, customerId) =>
		axios.get("/api/method/aims_customization.api.mss_monthly_schedule.get_customers", {
			params: {
				search_text: search,
				customer_id: customerId,
			},
		}),

	getBlanketOrders: (filters) =>
		axios.get("/api/method/aims_customization.api.mss_monthly_schedule.get_blanket_orders", {
			params: {
				customer: filters.customer,
				month: filters.month,
				year: filters.year,
				// search_text will be null/undefined, allowing the backend to handle the search logic
			},
		}),

	getBlanketOrdersSearch: (search) =>
		axios.get("/api/method/aims_customization.api.mss_monthly_schedule.get_blanket_orders", {
			params: { search_text: search },
		}),

	// -------------------- Level 2 --------------------
	getBlanketOrderItems(bo_list) {
		return axios.get(
			"/api/method/aims_customization.api.mss_monthly_schedule.get_items_for_blanket_orders",
			{
				params: { bo_list: JSON.stringify(bo_list) }, // <— FIX
			}
		);
	},
	getBlanketOrdersWithItems(filters) {
		return axios.get(
			"/api/method/aims_customization.api.mss_monthly_schedule.get_blanket_orders_with_items",
			{
				params: {
					customer: filters.customer,
					// search_text will be null/undefined, allowing the backend to handle the search logic
				},
			}
		);
	},
	createSalesOrderFromBOItems: (items) =>
		axios.post(
			"/api/method/aims_customization.api.mss_monthly_schedule.create_sales_order",
			{ items },
			{ headers: { "X-Frappe-CSRF-Token": frappe.csrf_token } }
		),

	// -------------------- Level 3 --------------------
	getSalesOrders: (filters, bo_list) =>
		axios.get("/api/method/aims_customization.api.mss_monthly_schedule.get_sales_orders", {
			params: {
				customer: filters.customer,
				month: filters.month,
				year: filters.year,
				bo_list: bo_list,
			},
		}),

	// -------------------- Level 4 --------------------
	getBOMsForSalesOrder: (sales_orders) =>
		axios.get(
			"/api/method/aims_customization.api.mss_monthly_schedule.get_boms_for_sales_orders",
			{
				params: { sales_orders: JSON.stringify(sales_orders) },
			}
		),

	// -------------------- Level 5 --------------------
	getRawMaterialsForBOMs: (boms) =>
		axios.get(
			"/api/method/aims_customization.api.mss_monthly_schedule.get_raw_materials_for_boms",
			{
				params: { boms: JSON.stringify(boms) },
			}
		),

	// -------------------- Capacity Planner Section --------------------
	getCapacityPlan: (payload) =>
		axios.post(
			"/api/method/aims_customization.api.mss_monthly_schedule.get_capacity_plan",
			{ payload_json: JSON.stringify(payload) },
			{ headers: { "X-Frappe-CSRF-Token": frappe.csrf_token } }
		),

	getShifts() {
		return axios.get("/api/resource/Shift Type", {
			params: { fields: ["name", "start_time", "end_time"] },
		});
	},
	createMSSPlan: ({ lines, filters, plan_start_date, plan_end_date, production_utilization }) =>
		axios.post(
			"/api/method/aims_customization.api.mss_monthly_schedule.create_mss_plan",
			{
				payload_json: JSON.stringify({
					lines,
					filters,
					plan_start_date,
					plan_end_date,
					production_utilization,
				}),
			},
			{
				headers: { "X-Frappe-CSRF-Token": frappe.csrf_token },
				withCredentials: true,
			}
		),

	getWorkstations: () =>
		axios.get("/api/method/aims_customization.api.mss_monthly_schedule.get_workstations"),
	// --------------------------- new work order and validate capacity ---------------------------
	validateCapacity: (payload) =>
		axios.post(
			"/api/method/aims_customization.api.mss_monthly_schedule.validate_capacity",
			{
				payload: JSON.stringify(payload), // ← correct
			},
			{ headers: { "X-Frappe-CSRF-Token": frappe.csrf_token } }
		),
	createWorkOrdersFromMSS: (payload) =>
		axios.post(
			"/api/method/aims_customization.api.mss_monthly_schedule.create_work_orders_from_mss",
			{ payload: JSON.stringify(payload) },
			{
				headers: { "X-Frappe-CSRF-Token": frappe.csrf_token },
				withCredentials: true,
			}
		),

	previewCapacityPlan: (payload) =>
		axios.post(
			"/api/method/aims_customization.api.mss_monthly_schedule.preview_capacity_plan",
			{ payload: JSON.stringify(payload) },
			{ headers: { "X-Frappe-CSRF-Token": frappe.csrf_token } }
		),
	// -------------------- Level 6 --------------------

	getWorkOrders: (so_list) =>
		axios.get(
			"/api/method/aims_customization.api.mss_monthly_schedule.get_work_orders_for_so",
			{
				params: { so_list: JSON.stringify(so_list) },
			}
		),
	// -------------------- Level 7 --------------------
	getJobCards: (wo_list) =>
		axios.get(
			"/api/method/aims_customization.api.mss_monthly_schedule.get_job_cards_for_work_orders",
			{
				params: { wo_list: JSON.stringify(wo_list) },
			}
		),

	// -------------------- Level 8: Production Summary --------------------
	getProductionSummary(customer, month, year) {
		// if (!customer || !month || !year) {
		// 	return Promise.reject(new Error("Customer, month and year are required"));
		// }

		return axios.get(
			"/api/method/aims_customization.api.mss_monthly_schedule.get_production_summary",
			{
				params: { customer: customer, month: month, year: year },
			}
		);
	},
	getProductionSummary(customer, month, year, options = {}) {
		return axios.get(
			"/api/method/aims_customization.api.mss_monthly_schedule.get_production_summary",
			{
				params: { customer, month, year },
				signal: options.signal,
			}
		);
	},
};
