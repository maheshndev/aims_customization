<template>
  <div class="blanket-order-items p-2 shadow-md border border-gray-200 rounded-lg">

    <!-- Top Controls -->
    <div
      class="sticky top-0 bg-white z-20 flex flex-col md:flex-row justify-between items-start md:items-center p-4 border-b border-gray-200 gap-3">

      <div class="flex flex-wrap items-center gap-2">
        <button @click="selectAll"
          class="px-3 py-1 bg-blue-600 text-black rounded hover:bg-blue-700 transition text-sm m-1">
          Select All
        </button>

        <button @click="unselectAll"
          class="px-3 py-1 bg-gray-300 text-gray-800 rounded hover:bg-gray-400 transition text-sm m-1">
          Unselect All
        </button>

        <span class="text-xs text-gray-500">{{ selectedItems.length }} selected</span>
      </div>

      <button v-if="selectedItems.length" @click="createSalesOrder"
        class="px-4 py-2 bg-black text-black rounded-lg hover:bg-gray-800 transition text-sm m-1">
        Create Sales Orders
      </button>
    </div>

    <!-- Loader -->
    <div v-if="loading" class="text-gray-500 animate-pulse py-6 text-center">
      Loading Finished Goods Items...
    </div>

    <!-- Error -->
    <div v-if="error" class="bg-red-100 text-red-700 px-4 py-2 border border-red-200 rounded mb-4 text-sm mx-4 mt-2">
      {{ error }}
    </div>

    <!-- Table -->
    <div v-if="items.length && !loading" class="overflow-auto rounded-b-2xl">
      <table class="min-w-[1200px] table-auto divide-y divide-gray-200 text-sm">
        <thead class="bg-gray-100 sticky top-0 z-10">
          <tr>
            <th class="px-2 py-2 text-left border w-16">Select</th>
            <th v-for="h in headers" :key="h" class="px-4 py-2 text-left font-medium text-gray-700 border whitespace-nowrap">
              {{ h }}
            </th>
          </tr>
        </thead>

        <tbody class="divide-y divide-gray-100">
          <tr v-for="item in items" :key="item.item_code" class="hover:bg-gray-50 transition">

            <!-- Checkbox -->
            <td class="px-2 py-1 text-center border whitespace-nowrap">
              <input type="checkbox" class="w-4 h-4" :value="item" v-model="selectedItems" @change="emitSelection" />
            </td>

            <!-- Dynamic Cells -->
            <td v-for="key in fieldKeys" :key="key" class="px-2 py-1 border text-gray-800 whitespace-nowrap">
              <!-- Editable schedule_qty -->
              <template v-if="key === 'schedule_qty'">
                <input type="number" v-model.number="item.schedule_qty" @input="emitSelection"
                  class="w-full border px-2 py-1 rounded" />
              </template>

              <!-- Readonly fields -->
              <template v-else>
                {{ item[key] }}
              </template>
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
    selectedBoNames: Array,
    selected: Array,
  },

  setup(props, { emit }) {
    const items = ref([]);
    const selectedItems = ref([]);
    const loading = ref(false);
    const error = ref(null);

    const headers = [
      "Blanket Order No.", "Item Code", "Item Name", "Qty", "Schedule Qty", "Rate",
      "Cavity", "PCS Wt", "Runner Wt", "Shot Wt", "Cycle Time",
      "Per Piece Wt (Incl. Runner Wt.)", "Available Stock (Nos.)", "Available Stock Amt",
      "Produced Stock (Nos.)", "Produced Stock Amt", "WIP Stock (Nos.)", "Wip Stock Amt",
      "Balance Produce Qty", "Balance Produce Amt",
      "Balance Deliver Qty", "Balance Deliver Amt", "Reserved Qty", "Incoming Qty",
      "BOM No", "Warehouse", "Dispatched Nos", "Dispatched Amt", "Total Stock Nos",
      "Total Stock Amt", "Total + Produced Nos", "Total + Produced Amt"
    ];

    const fieldKeys = [
      "bo_name", "item_code", "item_name", "order_qty", "schedule_qty", "rate",
      "cavity", "pcs_wt", "runner_wt", "shot_wt", "cycle_time",
      "weight_per_unit", "available_stock_nos", "available_stock_amt",
      "produced_stock_nos", "produced_stock_amt", "wip_stock_nos", "wip_stock_amt",
      "balance_to_produce_qty", "balance_to_produce_amt",
      "balance_to_deliver_qty", "balance_to_deliver_amt",
      "reserved_qty", "incoming_qty", "bom_no", "warehouse",
      "dispatched_qty_nos", "dispatched_amt", "total_stock_nos",
      "total_stock_amt", "total_plus_produced_nos", "total_plus_produced_amt"
    ];

    // Load BO Items
    const loadItems = async () => {
      loading.value = true;
      error.value = null;

      try {
        const res = await api.getBlanketOrderItems(props.selectedBoNames);
        items.value = res.data.message || [];
      } catch (err) {
        error.value = "Failed to load items.";
      }

      loading.value = false;
    };

    // Emit selection + updated quantities
    const emitSelection = () => {
      emit("update:selected", selectedItems.value);
    };

    const selectAll = () => {
      selectedItems.value = [...items.value];
      emitSelection();
    };

    const unselectAll = () => {
      selectedItems.value = [];
      emitSelection();
    };

    // Create Sales Order
    const createSalesOrder = async () => {
      if (!selectedItems.value.length) return;

      const payload = selectedItems.value.map(item => ({
        bo_name: item.bo_name,
        item_code: item.item_code,
        schedule_qty: Number(item.schedule_qty),  // IMPORTANT
        rate: item.rate,
        bom_no: item.bom_no
      }));

      try {
        const res = await api.createSalesOrderFromBOItems(payload);

        frappe.msgprint({
          title: res.data.message.status,
          message: res.data.message.message,
          indicator: "green",
        });

        selectedItems.value = [];
        emit("update:selected", []);
      } catch (err) {
        frappe.msgprint({
          title: "Error",
          message: "Failed to create Sales Order.",
          indicator: "red",
        });
      }
    };

    watch(
      () => props.selectedBoNames,
      (v) => {
        if (v && v.length) loadItems();
        else {
          items.value = [];
          selectedItems.value = [];
        }
      },
      { immediate: true }
    );


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
      emitSelection,
    };
  },
};
</script>
