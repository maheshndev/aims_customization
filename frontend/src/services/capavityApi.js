import axios from "axios";

export const api = {
	// -------------------- Capacity Monthly --------------------
	getCustomerList: (search = "", customerId) =>
		axios.get("/api/method/aims_customization.api.mss_capacity_monthly.get_customer_list", {
			params: { search_text: search, customer_id: customerId },
		}),

	getMachineCapacityMonthly: (filters) =>
		axios.post(
			"/api/method/aims_customization.api.mss_capacity_monthly.get_machine_capacity_monthly",
			{
				customer: filters.customer,
				month: filters.month,
				year: filters.year,
			},
			{ headers: { "X-Frappe-CSRF-Token": frappe.csrf_token } }
		),

	// -------------------- Item Capacity Monthly --------------------
	getItemCapacityMonthly: (filters) =>
		axios.post(
			"/api/method/aims_customization.api.mss_capacity_monthly.get_item_capacity_monthly",
			{
				customer: filters.customer,
				month: filters.month,
				year: filters.year,
				machines: filters.machines,
			},
			{ headers: { "X-Frappe-CSRF-Token": frappe.csrf_token } }
		),
};
