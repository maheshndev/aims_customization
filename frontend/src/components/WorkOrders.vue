<template>
  <div class="work-orders bg-white rounded shadow-sm p-4">

    <!-- Loading -->
    <div v-if="loading" class="text-gray-500">Loading Work Orders...</div>

    <!-- Error -->
    <div v-if="error" class="text-red-500 mb-2">{{ error }}</div>

    <!-- Table -->
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
          <tr
            v-for="wo in workOrders"
            :key="wo.name"
            class="hover:bg-gray-50 cursor-pointer"
            @click="selectWorkOrder(wo)"
          >
            <td class="border px-3 py-2">{{ wo.wo_no }}</td>
            <td class="border px-3 py-2">{{ wo.bo_name }}</td>
            <td class="border px-3 py-2">{{ wo.item_name }}</td>
            <td class="border px-3 py-2">{{ wo.qty }}</td>
            <td class="border px-3 py-2">{{ wo.planned_date }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- No Data -->
    <div v-if="!workOrders.length && !loading" class="text-gray-500 mt-2">
      No Work Orders found.
    </div>

  </div>
</template>

<script>
import {api} from "../services/api"

export default {
  name: "WorkOrders",

  props: {
    soList: { type: Array, default: () => [] }
  },

  data() {
    return {
      workOrders: [],
      loading: false,
      error: null
    };
  },

  methods: {
    async fetchWorkOrders() {
      if (!this.soList.length) {
        this.workOrders = [];
        return;
      }

      this.loading = true;
      this.error = null;

      try {
        const res = api.getWorkOrders(soList)

        this.workOrders = res.data.message || [];
      } catch (err) {
        console.error(err);
        this.error = "Failed to fetch Work Orders.";
      } finally {
        this.loading = false;
      }
    },

    // Emit selected WO name as array `[wo.name]`
    selectWorkOrder(wo) {
      this.$emit("wo-selected", [wo.name]);
    }
  },

  watch: {
    boList: {
      handler() {
        this.fetchWorkOrders();
      },
      deep: true,
      immediate: true
    }
  }
};
</script>
