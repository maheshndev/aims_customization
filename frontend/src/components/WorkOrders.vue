<template>
  <div class="work-orders bg-white rounded shadow-sm p-4">
    <div v-if="loading" class="text-gray-500">Loading Work Orders...</div>
    <div v-if="error" class="text-red-500 mb-2">{{ error }}</div>

    <div v-if="workOrders.length" class="overflow-x-auto">
      <table class="table-auto w-full border-collapse">
        <thead class="bg-gray-100">
          <tr>
            <th class="border px-3 py-2 text-left">WO</th>
            <th class="border px-3 py-2 text-left">BO</th>
            <th class="border px-3 py-2 text-left">Item</th>
            <th class="border px-3 py-2 text-left">Qty</th>
            <th class="border px-3 py-2 text-left">Planned Date</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="wo in workOrders" :key="wo.name" class="hover:bg-gray-50 cursor-pointer"
            @click="$emit('wo-selected', [wo.name])">
            <td class="border px-3 py-2">{{ wo.wo_no }}</td>
            <td class="border px-3 py-2">{{ wo.bo_name }}</td>
            <td class="border px-3 py-2">{{ wo.item_name }}</td>
            <td class="border px-3 py-2">{{ wo.qty }}</td>
            <td class="border px-3 py-2">{{ wo.planned_date }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="!workOrders.length && !loading" class="text-gray-500 mt-2">
      No Work Orders found.
    </div>
  </div>
</template>

<script>
import axios from "axios";

export default {
  name: "WorkOrders",
  props: { boList: { type: Array, default: () => [] } },
  data() {
    return { workOrders: [], loading: false, error: null };
  },
  methods: {
    async fetchWorkOrders() {
      if (!this.boList.length) {
        this.workOrders = [];
        return;
      }
      this.loading = true;
      this.error = null;
      try {
        const res = await axios.get(
          "/api/method/aims_customization.api.mss_monthly_schedule.get_work_orders",
          {
            params: { bo_list: JSON.stringify(this.boList) },
          },
        );
        this.workOrders = res.data.message || [];
      } catch (err) {
        console.error(err);
        this.error = "Failed to fetch Work Orders.";
      } finally {
        this.loading = false;
      }
    },
  },
  watch: {
    boList: {
      handler() {
        this.fetchWorkOrders();
      },
      deep: true,
      immediate: true,
    },
  },
};
</script>
