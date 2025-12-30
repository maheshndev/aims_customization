<template>
  <div class="blanket-orders  rounded-lg shadow-sm p-4">

    <div class="flex justify-between items-center mb-4">
      <div class="flex gap-2">
        <button @click="selectAll" class="px-3 py-1 bg-blue-100 text-black text-sm rounded hover:bg-blue-200 m-1">
          Select All
        </button>
        <button @click="unselectAll" class="px-3 py-1 bg-gray-200 text-black text-sm rounded hover:bg-gray-300 m-1">
          Unselect All
        </button>
      </div>
    </div>

    <div v-if="loading" class="text-gray-500 py-4 text-center animate-pulse">
      Loading Blanket Orders…
    </div>

    <div v-if="error" class="bg-red-50 border border-red-200 text-red-700 px-4 py-2 rounded mb-4">
      {{ error }}
    </div>

    <div v-if="orders.length && !loading" class="overflow-auto rounded-b-2xl">
      <table class="min-w-[1200px] table-auto border border-gray-300 divide-y divide-gray-200">
        <thead class="bg-gray-100 sticky uppercase">
          <tr>
            <th class="px-2 py-1 w-12 text-center border">
              <input type="checkbox" :checked="isAllSelected" @change="toggleAll" />
            </th>
            <th v-for="h in headers" :key="h"
              class="px-2 py-1 text-left text-sm font-medium text-gray-700 border whitespace-nowrap">
              {{ h }}
            </th>
          </tr>
        </thead>

        <tbody>
          <tr v-for="(bo, index) in orders"  :class="[
            'hover:bg-gray-50 transition',
            selectedBOrders.includes(bo.name) ? 'bg-blue-50' : ''
          ]">
            <td class="px-2 py-1 text-center border whitespace-nowrap">
              <input type="checkbox" v-model="selectedBOrders" :value="bo.name" :key="bo.name" />
            </td>
            <td class="px-2 py-1 text-sm border whitespace-nowrap">{{ index+1 }}</td>
            <td class="px-2 py-1 text-sm border whitespace-nowrap">{{ bo.name }}</td>
            <td class="px-2 py-1 text-sm border whitespace-nowrap">{{ bo.blanket_order_type }}</td>
            <td class="px-2 py-1 text-sm border whitespace-nowrap">{{ bo.customer }}</td>
            <td class="px-2 py-1 text-sm border whitespace-nowrap">{{ bo.order_date }}</td>
            <td class="px-2 py-1 text-sm border whitespace-nowrap">{{ bo.month }}</td>
            <td class="px-2 py-1 text-sm border whitespace-nowrap">{{ bo.from_date }}</td>
            <td class="px-2 py-1 text-sm border whitespace-nowrap">{{ bo.to_date }}</td>
            <td class="px-2 py-1 text-sm border whitespace-nowrap">{{ bo.company }}</td>
            <td class="px-2 py-1 text-sm border whitespace-nowrap">{{ bo.total_blanket_qty }}</td>
            <td class="px-2 py-1 text-sm border whitespace-nowrap">{{ bo.remaining_qty }}</td>
          </tr>
        </tbody>
      </table>
    </div>

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
      "#",
      "Blanket Order No.",
      "Type",
      "Customer",
      "Order Date",
      "Month",
      "From Date",
      "To Date",
      "Company",
      "Total Blanket Qty",
      "Remaining Qty"
    ];

    const isAllSelected = () =>
      orders.value.length && selectedBOrders.value.length === orders.value.length;

    const fetchBlanketOrders = async () => {
      loading.value = true;
      error.value = null;
      selectedBOrders.value = [];
      try {
        if(props.filters.customer || props.filters.month || props.filters.year){
        const res = await api.getBlanketOrders(props.filters);
        orders.value = res.data.message || [];
        }
        else{
            orders.value=[]
        }
      } catch (err) {
        error.value = "Failed to load Blanket Orders. Please try again.";
        orders.value = [];
      } finally {
        loading.value = false;
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
    };

    watch(() => props.filters, fetchBlanketOrders, { deep: true, immediate: true });

    watch(selectedBOrders, (val) => {
      const selectedBOs = orders.value.filter(bo => val.includes(bo.name));
      emit("update:selected", selectedBOs); 
    }, { deep: true });


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
