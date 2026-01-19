import axios from "axios";

export const api = {
	// -------------------- Capacity Monthly --------------------
	getCustomerList: (search = "", customerId) =>
		axios.get("/api/method/aims_customization.api.mss_capacity_monthly.get_customer_list", {
			params: { search_text: search, customer_id: customerId },
		}),

	getMachineCapacityMonthly: (filters) =>
		axios.get(
			"/api/method/aims_customization.api.mss_capacity_monthly.get_machine_capacity_monthly",
			{
				params: {
					customer: filters.customer || null,
					month: filters.month,
					year: filters.year,
					utilization: 90,
				},
			}
		),

	// -------------------- Item Capacity Monthly --------------------
	getItemCapacityMonthly: (filters, machines) =>
		axios.post(
			"/api/method/aims_customization.api.mss_capacity_monthly.get_item_capacity_monthly",
			{
				customer: filters?.customer || null,
				month: filters?.month || null,
				year: filters?.year || null,
				machines: machines || [],
			},
			{
				headers: {
					"X-Frappe-CSRF-Token": frappe.csrf_token,
				},
			}
		),
};
