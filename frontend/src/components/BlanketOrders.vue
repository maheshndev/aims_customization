<template>
  <div class="blanket-orders  rounded-lg shadow-sm p-4">

    <!-- Actions -->
    <div class="flex justify-between items-center mb-4">
      <div class="flex gap-2">
        <button @click="selectAll" class="px-3 py-1 bg-blue-600 text-black text-sm rounded hover:bg-blue-700">
          Select All
        </button>
        <button @click="unselectAll" class="px-3 py-1 bg-gray-700 text-black text-sm rounded hover:bg-black">
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
    <div v-if="orders.length && !loading" class="overflow-auto rounded-b-2xl">
      <table class="min-w-[1200px] table-auto border border-gray-300 divide-y divide-gray-200">
        <thead class="bg-gray-100 sticky">
          <tr>
            <th class="px-2 py-1 w-12 text-center border">
              <input type="checkbox" :checked="isAllSelected" @change="toggleAll" />
            </th>
            <th v-for="h in headers" :key="h" class="px-2 py-1 text-left text-sm font-medium text-gray-700 border whitespace-nowrap">
              {{ h }}
            </th>
          </tr>
        </thead>

        <tbody>
          <tr v-for="bo in orders" :key="bo.name" :class="[
            'hover:bg-gray-50 transition',
            selectedBOrders.includes(bo.name) ? 'bg-blue-50' : ''
          ]">
            <td class="px-2 py-1 text-center border whitespace-nowrap">
              <input type="checkbox" v-model="selectedBOrders" :value="bo.name" />
            </td>

            <td class="px-2 py-1 text-sm border whitespace-nowrap">{{ bo.name }}</td>
            <td class="px-2 py-1 text-sm border whitespace-nowrap">{{ bo.blanket_order_type }}</td>
            <td class="px-2 py-1 text-sm border whitespace-nowrap">{{ bo.customer }}</td>
            <td class="px-2 py-1 text-sm border whitespace-nowrap">{{ bo.customer_name }}</td>
            <td class="px-2 py-1 text-sm border whitespace-nowrap">{{ bo.order_no }}</td>
            <td class="px-2 py-1 text-sm border whitespace-nowrap">{{ bo.order_date }}</td>
            <td class="px-2 py-1 text-sm border whitespace-nowrap">{{ bo.month }}</td>
            <td class="px-2 py-1 text-sm border whitespace-nowrap">{{ bo.from_date }}</td>
            <td class="px-2 py-1 text-sm border whitespace-nowrap">{{ bo.to_date }}</td>
            <td class="px-2 py-1 text-sm border whitespace-nowrap">{{ bo.company }}</td>
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
import { ref, watch } from "vue";
import { api } from "../services/api";

export default {
  name: "BlanketOrders",

  props: {
    filters: { type: Object, required: true },
    selected: { type: Array, default: () => [] }, // v-model for selected BOs
  },

  setup(props, { emit }) {
    const orders = ref([]);
    const selectedBOrders = ref([]);
    const loading = ref(false);
    const error = ref(null);

    const headers = [
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
    ];

    const isAllSelected = () =>
      orders.value.length && selectedBOrders.value.length === orders.value.length;

    const fetchBlanketOrders = async () => {
      loading.value = true;
      error.value = null;
      selectedBOrders.value = [];
      try {
        const res = await api.getBlanketOrders(props.filters);
        orders.value = res.data.message || [];
      } catch (err) {
        error.value = "Failed to load Blanket Orders. Please try again.";
        orders.value = [];
      } finally {
        loading.value = false;
      }
    };

    const loadSelectedItems = async () => {
  if (!selectedBOrders.value.length) {
    emit("bo-loaded", []);
    emit("update:selected", []); // reset BO selection
    return;
  }

  try {
    const res = await api.getBlanketOrderItems(selectedBOrders.value);

    const combinedItems = res.data.message || [];

    // send BO ITEMS to parent
    emit("bo-loaded", combinedItems);

    // send selected BO objects
    const selectedBOs = orders.value.filter(bo =>
      selectedBOrders.value.includes(bo.name)
    );

    emit("update:selected", selectedBOs);  // BO list only
  } catch (err) {
    console.error("Failed to load BO items", err);
    emit("bo-loaded", []);
  }
};


    const toggleAll = (e) => {
      if (e.target.checked) selectAll();
      else unselectAll();
    };

    const selectAll = () => {
      selectedBOrders.value = orders.value.map(o => o.name);
    };

    const unselectAll = () => {
      selectedBOrders.value = [];
      emit("bo-loaded", []);
      emit("update:selected", []);
    };

    // Watch filters → fetch Blanket Orders automatically
    watch(() => props.filters, fetchBlanketOrders, { deep: true, immediate: true });

    // Watch selected BO names → fetch items automatically
    watch(selectedBOrders, loadSelectedItems, { deep: true });

    return {
      orders,
      selectedBOrders,
      loading,
      error,
      headers,
      isAllSelected,
      toggleAll,
      selectAll,
      unselectAll,
    };
  },
};
</script>
