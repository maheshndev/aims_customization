import axios from "axios";

export const api = {
  // -------------------- Capacity Monthly --------------------
  getCustomerList: () =>
    axios.get("/api/method/aims_customization.api.mss_capacity_monthly.get_customer_list"),
  
  getMachineCapacityMonthly: (filters) =>
    axios.post("/api/method/aims_customization.api.mss_capacity_monthly.get_machine_capacity_monthly",{
      customer : filters.customer,
      month: filters.month,
      year: filters.year,
    }),
 
  // -------------------- Item Capacity Monthly --------------------
  getItemCapacityMonthly: (filters) =>
    axios.post("/api/method/aims_customization.api.mss_capacity_monthly.get_item_capacity_monthly", {
      customer : filters.customer,
      month: filters.month,
      year: filters.year,
    }),
}
