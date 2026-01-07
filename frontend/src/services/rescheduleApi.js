import axios from "axios";


export const mssApi = {

  load(from, to) {
    return axios.post(
      "/api/method/aims_customization.api.mss_rescheduler_api.get_mss_schedule_range",
      {
        from_date: from,
        to_date: to
      },
	  {
				headers: {
					"X-Frappe-CSRF-Token": frappe.csrf_token,
				},
			}
    );
  },

  reschedule(payload) {
    return axios.post(
      "/api/method/aims_customization.api.mss_rescheduler_api.mss_reschedule",
      payload,
	  {
				headers: {
					"X-Frappe-CSRF-Token": frappe.csrf_token,
				},
			}
    );
  }
};
