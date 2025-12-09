<template>
  <div class="blanket-orders bg-white rounded-lg shadow-sm p-4">

    <!-- Actions -->
    <div class="flex justify-between items-center mb-4">
      <div class="flex gap-2">
        <button @click="selectAll" class="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700">
          Select All
        </button>

        <button @click="unselectAll" class="px-3 py-1 bg-gray-700 text-white text-sm rounded hover:bg-black">
          Unselect All
        </button>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="text-gray-500 py-4 text-center animate-pulse">
      Loading Blanket Orders…
    </div>

    <!-- Error -->
    <div v-if="error" class="bg-red-50 border border-red-200 text-red-700 px-4 py-2 rounded mb-4">
      {{ error }}
    </div>

    <!-- Table -->
    <div v-if="orders.length && !loading" class="overflow-x-auto">
      <table class="min-w-full border border-gray-300 divide-y divide-gray-200">
        <thead class="bg-gray-100">
          <tr>
            <th class="px-2 py-1 w-12 text-center border">
              <input type="checkbox" :checked="isAllSelected" @change="toggleAll" />
            </th>

            <th v-for="h in headers" :key="h"
              class="px-2 py-1 text-left text-sm font-medium text-gray-700 border">
              {{ h }}
            </th>
          </tr>
        </thead>

        <tbody>
          <tr v-for="bo in orders" :key="bo.name" :class="[
            'hover:bg-gray-50 transition',
            selectedOrders.includes(bo.name) ? 'bg-blue-50' : ''
          ]">

            <td class="px-2 py-1 text-center border">
              <input type="checkbox" v-model="selectedOrders" :value="bo.name" @change="handleSelection" />
            </td>

            <td class="px-2 py-1 text-sm border">{{ bo.name }}</td>
            <td class="px-2 py-1 text-sm border">{{ bo.blanket_order_type }}</td>
            <td class="px-2 py-1 text-sm border">{{ bo.customer }}</td>
            <td class="px-2 py-1 text-sm border">{{ bo.customer_name }}</td>
            <td class="px-2 py-1 text-sm border">{{ bo.order_no }}</td>
            <td class="px-2 py-1 text-sm border">{{ bo.order_date }}</td>
            <td class="px-2 py-1 text-sm border">{{ bo.month }}</td>
            <td class="px-2 py-1 text-sm border">{{ bo.from_date }}</td>
            <td class="px-2 py-1 text-sm border">{{ bo.to_date }}</td>
            <td class="px-2 py-1 text-sm border">{{ bo.company }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Empty State -->
    <div v-if="!orders.length && !loading" class="text-center text-gray-500 py-6">
      No Blanket Orders Found.
    </div>
  </div>
</template>

<script>
import { api } from "../services/api";

export default {
  name: "BlanketOrders",

  props: {
    filters: { type: Object, required: true },
    selected: { type: Array, default: () => [] }, // v-model for selected BOs
  },

  data() {
    return {
      orders: [],
      selectedOrders: [],
      loading: false,
      error: null,

      headers: [
        "Blanket Order No.",
        "Type",
        "Customer",
        "Customer Name",
        "Order No",
        "Order Date",
        "Month",
        "From Date",
        "To Date",
        "Company",
      ],
    };
  },

  computed: {
    isAllSelected() {
      return this.orders.length > 0 && this.selectedOrders.length === this.orders.length;
    },
  },

  watch: {
    filters: {
      deep: true,
      handler() {
        this.fetchBlanketOrders();
      },
    },
  },

  methods: {
    async fetchBlanketOrders() {
      this.loading = true;
      this.error = null;
      this.selectedOrders = [];

      try {
        const res = await api.getBlanketOrders({
          customer: this.filters.customer,
          month: this.filters.month,
          year: this.filters.year,
          blanket_order: this.filters.blanket_order,
        });

        this.orders = res.data.message || [];
        this.$emit("blanket-orders-loaded", this.orders);

      } catch (err) {
        this.error = "Failed to load Blanket Orders. Please try again.";
      } finally {
        this.loading = false;
      }
    },

    toggleAll(e) {
      if (e.target.checked) this.selectAll();
      else this.unselectAll();
    },

    selectAll() {
      this.selectedOrders = this.orders.map(o => o.name);
      this.processSelectedOrders();
    },

    unselectAll() {
      this.selectedOrders = [];
      this.$emit("update:selected", []);
      this.$emit("items-loaded", []);
    },

    async handleSelection() {
      this.processSelectedOrders();
    },

    async processSelectedOrders() {
      let combinedItems = [];

      if (this.selectedOrders.length) {
        const res = await api.getBlanketOrderItems({ bo_list: this.selectedOrders });
        combinedItems = res.data.message || [];
      }

      // Emit to parent
      this.$emit('update:selected', this.selectedOrders);
      this.$emit('items-loaded', combinedItems);
    },
  },

  mounted() {
    this.fetchBlanketOrders();
  },
};
</script>
