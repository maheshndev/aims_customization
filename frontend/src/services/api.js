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
				params: {bo_list: JSON.stringify(bo_list)} // <— FIX
			}
		);
	},

	createSalesOrderFromBOItems: ( items) =>
		axios.post("/api/method/aims_customization.api.mss_monthly_schedule.create_sales_order", 
			{ items }
		,{ headers: { "X-Frappe-CSRF-Token": frappe.csrf_token }
    }),

	// -------------------- Level 3 --------------------
	getSalesOrders: (customer) =>
		axios.get("/api/method/aims_customization.api.mss_monthly_schedule.get_sales_orders", {
			params: {customer}
		}),

	// -------------------- Level 4 --------------------
	getBOMsForSalesOrder: (sales_orders) =>
		axios.get("/api/method/aims_customization.api.mss_monthly_schedule.get_boms_for_sales_orders", {
			params: { sales_orders: JSON.stringify(sales_orders) },
		}),
 
	// -------------------- Level 5 --------------------
	getRawMaterialsForBOMs: (boms) =>
		axios.get(
			"/api/method/aims_customization.api.mss_monthly_schedule.get_raw_materials_for_boms",
			{
				params: { boms: JSON.stringify(boms) },
			}
		),
	
	// -------------------- Level 6 --------------------
	getWorkOrders: (bo_list) =>
		axios.get(
			"/api/method/aims_customization.api.mss_monthly_schedule.get_work_orders_for_blanket_orders",
			{
				params: { bo_list: JSON.stringify(bo_list) },
			}
		),

	createWorkOrders: (bo_list) =>
		axios.post("/api/method/aims_customization.api.mss_monthly_schedule.create_work_orders", 	
			{ bo_list }
		,{ headers: { "X-Frappe-CSRF-Token": frappe.csrf_token }
		}),

	// -------------------- Level 7 --------------------
	getJobCards: (wo_list) =>
		axios.get(
			"/api/method/aims_customization.api.mss_monthly_schedule.get_job_cards_for_work_orders",
			{
				params: { wo_list : JSON.stringify(wo_list) },
			}
		),

	attachQCJobCard: (job_card, qc_item_code) =>
		axios.post("/api/method/aims_customization.api.mss_monthly_schedule.attach_qc_job_card", {
			job_card,
			qc_item_code,
		}),

	addScrapJobCard: (job_card, scrap_qty) =>
		axios.post("/api/method/aims_customization.api.mss_monthly_schedule.add_scrap_job_card", {
			job_card,
			scrap_qty,
		}),

	updateJobCardStatus: (job_card, status) =>
		axios.post(
			"/api/method/aims_customization.api.mss_monthly_schedule.update_job_card_status",
			{
				job_card,
				status,
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
