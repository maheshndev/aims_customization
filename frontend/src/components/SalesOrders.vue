<template>
  <div class="sales-orders bg-white rounded shadow-sm p-4">
    <div v-if="loading" class="text-gray-500">Loading Sales Orders...</div>
    <div v-if="error" class="text-red-500 mb-2">{{ error }}</div>

    <div v-if="orders.length" class="overflow-x-auto">
      <table class="table-auto w-full border-collapse">
        <thead class="bg-gray-100">
          <tr>
            <th class="border px-3 py-2 text-left">SO</th>
            <th class="border px-3 py-2 text-left">Customer</th>
            <th class="border px-3 py-2 text-left">BO</th>
            <th class="border px-3 py-2 text-left">Item</th>
            <th class="border px-3 py-2 text-right">Qty</th>
            <th class="border px-3 py-2 text-left">Delivery Date</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="so in orders" :key="so.name" class="hover:bg-gray-50">
            <td class="border px-3 py-2">{{ so.sales_order }}</td>
            <td class="border px-3 py-2">{{ so.customer_name }}</td>
            <td class="border px-3 py-2">{{ so.bo_name }}</td>
            <td class="border px-3 py-2">{{ so.item_name }}</td>
            <td class="border px-3 py-2 text-right">{{ so.qty }}</td>
            <td class="border px-3 py-2">{{ so.delivery_date }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="!orders.length && !loading" class="text-gray-500 mt-2">
      No Sales Orders found.
    </div>
  </div>
</template>

<script>
import axios from "axios";

export default {
  name: "SalesOrders",
  props: { boList: { type: Array, default: () => [] } },
  data() {
    return { orders: [], loading: false, error: null };
  },
  methods: {
    async fetchOrders() {
      if (!this.boList.length) {
        this.orders = [];
        return;
      }
      this.loading = true;
      this.error = null;
      try {
        const response = await axios.get(
          "/api/method/aims_customization.api.mss_monthly_schedule.get_sales_orders",
          {
            params: { bo_list: JSON.stringify(this.boList) },
          },
        );
        this.orders = response.data.message || [];
      } catch (err) {
        console.error(err);
        this.error = "Failed to fetch Sales Orders.";
      } finally {
        this.loading = false;
      }
    },
  },
  watch: {
    boList: {
      handler() {
        this.fetchOrders();
      },
      deep: true,
      immediate: true,
    },
  },
};
</script>
