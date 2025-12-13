import axios from "axios";

export const api = {
	// -------------------- Level 1 --------------------
	getCustomers: (search) =>
		axios.get("/api/method/aims_customization.api.mss_monthly_schedule.get_customers", {
			params: { search_text: search },
		}),

	getBlanketOrders: (params) =>
		axios.get("/api/method/aims_customization.api.mss_monthly_schedule.get_blanket_orders", {
			params,
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

	createSalesOrderFromBOItems: (items) =>
		axios.post(
			"/api/method/aims_customization.api.mss_monthly_schedule.create_sales_order",
			{ items },
			{ headers: { "X-Frappe-CSRF-Token": frappe.csrf_token } }
		),

	// -------------------- Level 3 --------------------
	getSalesOrders: (params) =>
		axios.get("/api/method/aims_customization.api.mss_monthly_schedule.get_sales_orders", {
			params,
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
	createMSSPlan: ({ lines, filters }) => {
		return axios.post(
			"/api/method/aims_customization.api.mss_monthly_schedule.create_mss_plan",
			{
				payload_json: { lines, filters }, // send pure JSON
			},
			{
				headers: {
					"X-Frappe-CSRF-Token": frappe.csrf_token,
					"Content-Type": "application/json",
				},
				withCredentials: true,
			}
		);
	},

	getWorkstations: () =>
		axios.get("/api/method/aims_customization.api.mss_monthly_schedule.get_workstations"),

	validate_capacity: (payload) =>
		axios.post(
			"/api/method/aims_customization.api.mss_monthly_schedule.validate_capacity",
			{
				payload_json: JSON.stringify(payload), // ← correct
			},
			{
				headers: { "X-Frappe-CSRF-Token": frappe.csrf_token },
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

	createWorkOrders: (so_list) =>
		axios.post(
			"/api/method/aims_customization.api.mss_monthly_schedule.create_work_orders",
			{ so_list },
			{ headers: { "X-Frappe-CSRF-Token": frappe.csrf_token } }
		),

	// -------------------- Level 7 --------------------
	getJobCards: (wo_list) => 
	axios.get(
		"/api/method/aims_customization.api.mss_monthly_schedule.get_job_cards_for_work_orders",
		{
			params: { wo_list : JSON.stringify(wo_list) },
		}
	),
	
	// -------------------- Level 8 --------------------
	getProductionStatus: (bo_list) =>
		axios.get(
			"/api/method/aims_customization.api.mss_monthly_schedule.get_production_status",
			{
				params: { bo_list },
			}
		),
};
