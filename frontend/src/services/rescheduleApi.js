import axios from "axios";

export const api = {
	getWorkOrders: (so_list) =>
		axios.get(
			"/api/method/aims_customization.api.mss_rescheduler.get_work_orders_for_so",
			{
				params: { so_list: JSON.stringify(so_list) },
			}
		),
};
