<template>
  <div class="blanket-order-items  p-2 shadow-md border border-gray-200 rounded-lg">

    <!-- Top Controls (Sticky) -->
    <div class="sticky top-0 bg-white z-20 flex flex-col md:flex-row justify-between items-start md:items-center p-4 border-b border-gray-200 gap-3">
      <div class="flex flex-wrap items-center gap-2">
        <button @click="selectAll"
          class="px-3 py-1 bg-blue-600 text-black rounded hover:bg-blue-700 transition text-sm">
          Select All
        </button>
        <button @click="unselectAll"
          class="px-3 py-1 bg-gray-300 text-gray-800 rounded hover:bg-gray-400 transition text-sm">
          Unselect All
        </button>
        <span class="text-xs text-gray-500">{{ selectedItems.length }} selected</span>
      </div>

      <button v-if="selectedItems.length" @click="createSalesOrder"
        class="px-4 py-2 bg-black text-black rounded-lg hover:bg-gray-800 transition text-sm">
        Create Sales Orders
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="text-gray-500 animate-pulse py-6 text-center">
      Loading Finished Goods Items...
    </div>

    <!-- Error -->
    <div v-if="error" class="bg-red-100 text-red-700 px-4 py-2 border border-red-200 rounded mb-4 text-sm mx-4 mt-2">
      {{ error }}
    </div>

    <!-- Table Wrapper -->
    <div v-if="items.length && !loading" class="overflow-auto rounded-b-2xl">
      <table class="min-w-[1200px] table-auto divide-y divide-gray-200 text-sm">
        <thead class="bg-gray-100 sticky top-0 z-10">
          <tr>
            <th class="px-2 py-2 text-left border w-16">Select</th>
            <th v-for="h in headers" :key="h"
              class="px-4 py-2 text-left font-medium text-gray-700 border whitespace-nowrap">
              {{ h }}
            </th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-100">
          <tr v-for="item in items" :key="item.item_code" class="hover:bg-gray-50 transition">
            <td class="px-2 py-1 text-center border">
              <input type="checkbox" class="w-4 h-4" :value="item" v-model="selectedItems" />
            </td>
            <td v-for="key in fieldKeys" :key="key" class="px-2 py-1 border text-gray-800 whitespace-nowrap">
              {{ item[key] }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- No Items -->
    <div v-if="selectedBoNames.length && !items.length && !loading" class="text-gray-500 mt-4 text-center text-sm px-4">
      No Finished Goods items found for the selected Blanket Orders.
    </div>

  </div>
</template>

<script>
import { ref, watch } from "vue";
import { api } from "../services/api";

export default {
  name: "BlanketOrderItems",
  props: {
    selectedBoNames: { type: Array, default: () => [] },
    selected: { type: Array, default: () => [] },
  },
  setup(props, { emit }) {
    const items = ref([]);
    const selectedItems = ref([]);
    const loading = ref(false);
    const error = ref(null);

    const headers = [
      "Blanket Order No.", "Item Code", "Item Name", "Qty", "Rate",
      "Cavity", "PCS Wt", "Runner Wt", "Shot Wt", "Cycle Time",
      "Per Piece Wt (Incl. Runner Wt.)", "Available Stock (Nos.)",
      "Produced Stock (Nos.)", "WIP Stock (Nos.)", "Balance Produce",
      "Balance Deliver"
    ];

    const fieldKeys = [
      "bo_name", "item_code", "item_name", "order_qty", "rate",
      "cavity", "pcs_wt", "runner_wt", "shot_wt", "cycle_time",
      "weight_per_unit", "available_stock_nos",
      "produced_stock_nos", "wip_stock_nos", "balance_to_produce_qty",
      "balance_to_deliver_qty"
    ];

    const loadItems = async () => {
      if (!props.selectedBoNames.length) return;
      loading.value = true;
      error.value = null;
      try {
        const res = await api.getBlanketOrderItems(props.selectedBoNames);
        items.value = res.data.message || [];
      } catch {
        error.value = "Failed to load items.";
      } finally {
        loading.value = false;
      }
    };

    const selectAll = () => { selectedItems.value = [...items.value]; };
    const unselectAll = () => { selectedItems.value = []; };

    const createSalesOrder = async () => {
      if (!selectedItems.value.length) return;
      try {
        const res = await api.createSalesOrderFromBOItems(selectedItems.value);
        frappe.msgprint({
          title: res.data.message.status,
          message: res.data.message.message,
          indicator: res.data.message.sales_orders,
        });
        selectedItems.value = [];
        emit("update:selected", []);
      } catch (err) {
        frappe.msgprint({
          title: "Error",
          message: "Failed to create Sales Order.",
          indicator: "red",
        });
        console.error(err);
      }
    };

    watch(() => props.selectedBoNames, (list) => {
      if (list.length) loadItems();
      else { items.value = []; selectedItems.value = []; }
    }, { immediate: true });

    watch(selectedItems, val => emit("update:selected", val));

    return {
      items, selectedItems, loading, error,
      headers, fieldKeys,
      selectAll, unselectAll, createSalesOrder
    };
  },
};
</script>

<style scoped>
/* Scrollbar Styling */
.blanket-order-items::-webkit-scrollbar {
  height: 8px;
  width: 8px;
}
.blanket-order-items::-webkit-scrollbar-thumb {
  background-color: rgba(100, 100, 100, 0.4);
  border-radius: 4px;
}

/* Table Styles */
.blanket-order-items table {
  border-collapse: collapse;
}
.blanket-order-items th,
.blanket-order-items td {
  min-width: 120px;
}
@media (max-width: 768px) {
  .blanket-order-items th,
  .blanket-order-items td {
    min-width: 100px;
    font-size: 0.75rem;
  }
}
</style>
