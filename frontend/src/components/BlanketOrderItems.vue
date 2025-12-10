<template>
  <div class="blanket-order-items rounded-xl p-2 shadow-md overflow-x-auto">

    <!-- Top Controls -->
    <div class="flex flex-col md:flex-row justify-between items-start md:items-center mb-4 gap-3">
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
    <div v-if="loading" class="text-gray-500 animate-pulse py-4 text-center">
      Loading Finished Good Items...
    </div>

    <!-- Error -->
    <div v-if="error" class="bg-red-100 text-red-700 px-4 py-2 border border-red-200 rounded mb-4 text-sm">
      {{ error }}
    </div>

    <!-- Table Wrapper -->
    <div v-if="items.length && !loading" class="overflow-x-auto rounded-lg border border-gray-200 shadow-sm">
      <table class="min-w-[650px] table-auto divide-y divide-gray-200 text-sm">
        <thead class="bg-gray-100">
          <tr>
            <th class="px-1 py-1 text-left border w-16">Select</th>
            <th v-for="h in headers" :key="h" class="px-1 py-2 text-left font-medium text-gray-700 border w-[250px]" width="250px">
              {{ h }}
            </th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-100">
          <tr v-for="item in items" :key="item.item_code" class="hover:bg-gray-50 transition">
            <td class="px-2 py-1 text-center border">
              <input type="checkbox" class="w-4 h-4" :value="item" v-model="selectedItems" />
            </td>
            <td v-for="key in fieldKeys" :key="key" class="px-2 py-1 border text-gray-800 w-[280px] break-words">
              {{ item[key] }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- No Items -->
    <div v-if="selectedBoNames.length && !items.length && !loading" class="text-gray-500 mt-4 text-center text-sm">
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
      "Blanket Order No.",
      "Item Code",
      "Item Name",
      "Qty",
      "Rate",
      "Cavity",
      "PCS Wt",
      "Runner Wt",
      "Shot Wt",
      "Cycle Time",
      "Per Piece Wt (Incl. Runner Wt.)",
      "Available Stock (Nos.)",
      "Available Stock (Amt.)",
      "Delivered Qty (Nos.)",
      "Available Stock",
      "Produced Stock",
      "WIP Stock",
      "Balance Produce",
      "Balance Deliver",
    ];

    const fieldKeys = [
      "bo_name",
      "item_code",
      "item_name",
      "order_qty",
      "rate",
      "cavity",
      "pcs_wt",
      "runner_wt",
      "shot_wt",
      "cycle_time",
      "weight_per_unit",
      "available_stock_nos",
      "produced_stock_nos",
      "wip_stock_nos",
      "balance_to_produce_qty",
      "balance_to_deliver_qty",
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

    const selectAll = () => {
      selectedItems.value = [...items.value];
    };

    const unselectAll = () => {
      selectedItems.value = [];
    };

    const createSalesOrder = async () => {
      if (!selectedItems.value.length) return;

      try {
        // Assuming selectedBoNames[0] is the blanket order to create SO for
        const blanketOrder = props.selectedBoNames[0];
        const items = selectedItems.value;

        const res = await api.createSalesOrderFromBOItems(items);
         console.log(res);
         
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


    watch(
      () => props.selectedBoNames,
      (list) => {
        if (list.length) loadItems();
        else {
          items.value = [];
          selectedItems.value = [];
        }
      },
      { immediate: true }
    );

    watch(selectedItems, (val) => emit("update:selected", val));

    return {
      items,
      selectedItems,
      loading,
      error,
      headers,
      fieldKeys,
      selectAll,
      unselectAll,
      createSalesOrder,
    };
  },
};
</script>

<style scoped>
/* Optional: Add smooth scrolling for horizontal scroll on small devices */
.blanket-order-items::-webkit-scrollbar {
  height: 8px;
}

.blanket-order-items::-webkit-scrollbar-thumb {
  background-color: rgba(100, 100, 100, 0.4);
  border-radius: 4px;
}
</style>
