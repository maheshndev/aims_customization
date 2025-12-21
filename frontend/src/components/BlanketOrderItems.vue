<template>
  <div class="blanket-order-items p-2 shadow-md border border-gray-200 rounded-lg">

    <!-- ================= TOP CONTROLS ================= -->
    <div
      class=" top-0 bg-white z-20 flex flex-col md:flex-row justify-between items-start md:items-center p-4 border-b border-gray-200 gap-3">

      <div class="flex flex-wrap items-center gap-2">
        <button @click="selectAll"
          class="px-3 py-1 bg-blue-100 text-black rounded hover:bg-blue-200 transition text-sm">
          Select All
        </button>

        <button @click="unselectAll"
          class="px-3 py-1 bg-gray-200 text-gray-800 rounded hover:bg-gray-300 transition text-sm">
          Unselect All
        </button>

        <span class="text-xs text-gray-500">
          {{ selectedItems.length }} selected
        </span>

        <button v-if="selectedItems.length" @click="createSalesOrder"
          class="px-3 py-2 bg-indigo-100 text-black rounded-lg hover:bg-indigo-200 transition text-sm">
          Create Sales Orders
        </button>

        <!-- 🔍 Item Search -->
        <input v-model="searchText" type="text" placeholder="Search By: Item Name / Item Code / Blanket Order ID "
          class="px-3 py-2 border rounded-lg text-sm w-full md:w-64 focus:outline-none focus:ring focus:border-indigo-300" />
      </div>


    </div>

    <!-- ================= LOADER ================= -->
    <div v-if="loading" class="text-gray-500 animate-pulse py-6 text-center">
      Loading Finished Goods Items...
    </div>

    <!-- ================= ERROR ================= -->
    <div v-if="error" class="bg-red-100 text-red-700 px-4 py-2 border border-red-200 rounded mb-4 text-sm mx-4 mt-2">
      {{ error }}
    </div>

    <!-- ================= TABLE ================= -->
    <div v-if="filteredItems.length && !loading" class="overflow-auto rounded-b-2xl">
      <table class="min-w-[1200px] table-auto divide-y divide-gray-200 text-sm">
        <thead class="bg-gray-100 sticky top-0 z-10 uppercase">
          <tr>
            <th class="px-2 py-2 text-left border w-16">Select</th>
            <th class="px-2 py-2 text-left border w-16">#</th>
            <th v-for="h in headers" :key="h"
              class="px-2 py-2 text-left font-medium text-gray-700 border whitespace-nowrap">
              {{ h }}
            </th>
          </tr>
        </thead>

        <tbody class="divide-y divide-gray-100">
          <tr v-for="(item, index) in filteredItems" :key="item.bo_name + item.item_code" :class="[
            'hover:bg-gray-50 transition',
            selectedItems.includes(item) ? 'bg-blue-50' : ''
          ]">

            <!-- Checkbox -->
            <td class="px-1 py-1 text-center border">
              <input type="checkbox" class="w-4 h-4" :value="item" v-model="selectedItems" />
            </td>

            <!-- Index -->
            <td class="px-1 py-1 text-center border">
              {{ index + 1 }}
            </td>

            <!-- Dynamic Cells -->
            <td v-for="key in fieldKeys" :key="key" class="px-1 py-1 border text-gray-800 whitespace-nowrap">

              <!-- Editable Schedule Qty -->
              <template v-if="key === 'schedule_qty'">
                <input type="number" :min="0" :max="item.remaining_bo_qty" v-model.number="item.schedule_qty"
                  @input="validateScheduleQty(item)" class="w-full border px-2 py-1 rounded" />
              </template>

              <!-- Readonly Fields -->
              <template v-else>
                {{ item[key] }}
              </template>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- ================= EMPTY STATE ================= -->
    <div v-if="selectedBoNames.length && !filteredItems.length && !loading"
      class="text-gray-500 mt-4 text-center text-sm px-4">
      No items found for the selected Blanket Orders.
    </div>

  </div>
</template>

<script>
import { ref, watch, computed } from "vue";
import { api } from "../services/api";

export default {
  name: "BlanketOrderItems",

  props: {
    selectedBoNames: Array,
    selected: Array,
    filters: { type: Object, required: true },
  },

  setup(props, { emit }) {

    const items = ref([]);
    const selectedItems = ref([]);
    const loading = ref(false);
    const error = ref(null);
    const searchText = ref("");

    /* ================= TABLE HEADERS ================= */
    const headers = [
      "Customer",
      "Blanket Order No.",
      "Blanket Order Date",
      "Item Code",
      "Item Name",
      "Qty",
      "Pending To Produce Qty",
      "Schedule Qty",
      "Produced Qty",
      "Rate"
    ];

    const fieldKeys = [
      "customer",
      "bo_name",
      "order_date",
      "item_code",
      "item_name",
      "order_qty",
      "remaining_bo_qty",
      "schedule_qty",
      "consumed_qty",
      "rate"
    ];

    /* ================= FILTERED ITEMS ================= */
    const filteredItems = computed(() => {
      if (!searchText.value) return items.value;

      const q = searchText.value.toLowerCase();

      return items.value.filter(item =>
        item.item_code?.toLowerCase().includes(q) ||
        item.item_name?.toLowerCase().includes(q) ||
        item.bo_name?.toLowerCase().includes(q) ||
        item.customer?.toLowerCase().includes(q)
      );
    });

    /* ================= LOAD DATA ================= */
    const loadItems = async () => {
      loading.value = true;
      error.value = null;

      try {
        if (props.filters.customer) {
          const res = await api.getBlanketOrdersWithItems(props.filters);
          items.value = res?.data?.message || [];
        } else {
          items.value = [];
        }

      } catch (e) {
        error.value = "Failed to load items.";
      }

      loading.value = false;
    };

    /* ================= SELECTION ================= */
    const selectAll = () => {
      selectedItems.value = [...filteredItems.value];
    };

    const unselectAll = () => {
      selectedItems.value = [];
    };

    /* ================= CREATE SALES ORDER ================= */
    const createSalesOrder = async () => {
      if (!selectedItems.value.length) return;

      const payload = selectedItems.value.map(item => ({
        bo_name: item.bo_name,
        item_code: item.item_code,
        schedule_qty: Number(item.schedule_qty) || 0,
        rate: item.rate || 0,
        bom_no: item.bom_no || null,
        warehouse: item.warehouse || null
      }));

      try {

        const res = await api.createSalesOrderFromBOItems(payload);
        const data = res?.data?.message || {};

        if (!data.skipped?.length) {
          frappe.msgprint({
            title: "Success",
            indicator: "green",
            message: `
              ${data.message}
              <br><br>
              <b>Created:</b> ${data.created_sales_orders?.join(", ")}
            `
          });
        } else {
          frappe.msgprint({
            title: "Error",
            indicator: "red",
            message: `<b>${data.skipped[0].reason}</b>`
          });
        }

        selectedItems.value = [];
        emit("update:selected", []);

      } catch (err) {
        frappe.msgprint({
          title: "Error",
          indicator: "red",
          message: err?.message || "Failed to create Sales Order."
        });
      }
    };

    /* ================= WATCH ================= */
    // watch(
    //   () => props.selectedBoNames,
    //   (v) => {
    //     if (v && v.length) loadItems();
    //     else {
    //       items.value = [];
    //       selectedItems.value = [];
    //     }
    //   },
    //   { immediate: true }
    // );

    watch(
      () => props.filters,
      (newFilters) => {
        if (newFilters && Object.keys(newFilters).length) {
          loadItems();
        } else {
          items.value = [];
          selectedItems.value = [];
        }
      },
      { immediate: true, deep: true }
    );
    const validateScheduleQty = (item) => {
      if (item.schedule_qty == null) return;

      // Prevent negative values
      if (item.schedule_qty < 0) {
        item.schedule_qty = 0;
      }

      // Prevent exceeding order qty
      if (item.schedule_qty > item.remaining_bo_qty) {
        item.schedule_qty = item.remaining_bo_qty;

        frappe.msgprint({
          message: `Schedule Qty cannot exceed Pending to Produce Qty (${item.remaining_bo_qty})`,
          indicator: "orange"
        });
      }
    };


    return {
      items,
      filteredItems,
      selectedItems,
      loading,
      error,
      searchText,
      headers,
      fieldKeys,
      selectAll,
      unselectAll,
      createSalesOrder,
      validateScheduleQty
    };
  }
};
</script>

<style>
/* Custom styles only if required */
</style>
