import axios from "axios";

const headers = {
	"X-Frappe-CSRF-Token": frappe.csrf_token,
};

export const mssApi = {
	load(payload) {
		return axios.post(
			"/api/method/aims_customization.api.mss_rescheduler_api.get_mss_schedule_range",
			payload,
			{ headers }
		);
	},

	reschedule(payload) {
		return axios.post(
			"/api/method/aims_customization.api.mss_rescheduler_api.mss_reschedule",
			payload,
			{ headers }
		);
	},

	search(doctype, txt = "", limit = 20) {
		return axios.post(
			"/api/method/aims_customization.api.mss_rescheduler_api.mss_search_options",
			{ doctype, txt, limit },
			{ headers }
		);
	},

	getHolidays(from_date, to_date) {
		return axios.post(
			"/api/method/aims_customization.api.mss_rescheduler_api.get_holidays",
			{ from_date, to_date },
			{ headers }
		);
	},
};
