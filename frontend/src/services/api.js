import axios from "axios";

export const api = {
	// -------------------- Level 1 --------------------
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
					month: filters.month,
					year: filters.year,
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
				blanket_items: bo_list ? JSON.stringify(bo_list) : null,
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
	getShifts() {
		return axios.get("/api/resource/Shift Type", {
			params: { fields: ["name", "start_time", "end_time"] },
		});
	},
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
	getSmartSchedulePreview: (lines, planStart) =>
		axios.get(
			"/api/method/aims_customization.api.mss_monthly_schedule.get_smart_schedule_preview",
			{
				params: { lines: lines, plan_start_date: planStart },
			}
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
	getProductionControlDashboard(filters) {
		return axios.get(
			"/api/method/aims_customization.api.mss_monthly_schedule.get_production_control_dashboard",
			{ params: { customer: filters.customer, month: filters.month, year: filters.year } }
		);
	},
};
