<template>
  <div class="blanket-order-items p-2 shadow-md border border-gray-200 rounded-lg">
    <div
      class="top-0 bg-white z-20 flex flex-col md:flex-row justify-between items-start md:items-center p-4 border-b border-gray-200 gap-3">
      <div class="flex flex-wrap items-center gap-2">
        <button @click="selectAll"
          class="px-3 py-1 bg-blue-100 text-black rounded hover:bg-blue-200 transition text-sm">
          Select All
        </button>

        <button @click="unselectAll"
          class="px-3 py-1 bg-gray-200 text-gray-800 rounded hover:bg-gray-300 transition text-sm">
          Unselect All
        </button>
        <button class="px-3 py-1 bg-green-100 text-black rounded hover:bg-green-200" @click="refreshBOrders">
          🔄 Refresh
        </button>

        <span class="text-xs text-gray-500"> {{ selectedItems.length }} selected </span>

        <button v-if="selectedItems.length" @click="createSalesOrder"
          class="px-3 py-2 bg-indigo-100 text-black rounded-lg hover:bg-indigo-200 transition text-sm">
          Create Sales Orders
        </button>

        <input v-model="searchText" type="text" placeholder="Search By: Item Name / Item Code / Blanket Order ID "
          class="px-3 py-2 border rounded-lg text-sm w-full md:w-64 focus:outline-none focus:ring focus:border-indigo-300" />
      </div>
    </div>

    <div v-if="loading" class="text-gray-500 animate-pulse py-6 text-center">
      Loading Finished Goods Items...
    </div>

    <div v-if="error" class="bg-red-100 text-red-700 px-4 py-2 border border-red-200 rounded mb-4 text-sm mx-4 mt-2">
      {{ error }}
    </div>

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
            selectedItems.includes(item) ? 'bg-blue-50' : '',
          ]">
            <td class="px-1 py-1 text-center border">
              <input type="checkbox" class="w-4 h-4" :value="item" v-model="selectedItems" />
            </td>

            <td class="px-1 py-1 text-center border">
              {{ index + 1 }}
            </td>

            <td v-for="key in fieldKeys" :key="key" class="px-1 py-1 border text-gray-800 whitespace-nowrap">
              <template v-if="key === 'schedule_qty'">
                <input type="number" :min="0" :max="item.remaining_bo_qty" v-model.number="item.schedule_qty"
                  @input="validateScheduleQty(item)" class="w-full border px-2 py-1 rounded" />
              </template>
              <template v-else-if="key === 'bo_name'">
                <a class="cursor-pointer hover:underline hover:text-blue-600" :href="`/app/blanket-order/${item[key]}`"
                  target="_blank">{{ item[key] }}</a>
              </template>
              <template v-else>
                {{ item[key] }}
              </template>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

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
      "Rate",
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
      "rate",
    ];

    const filteredItems = computed(() => {
      if (!searchText.value) return items.value;

      const q = searchText.value.toLowerCase();

      return items.value.filter(
        (item) =>
          item.item_code?.toLowerCase().includes(q) ||
          item.item_name?.toLowerCase().includes(q) ||
          item.bo_name?.toLowerCase().includes(q) ||
          item.customer?.toLowerCase().includes(q)
      );
    });
    const showMessage = ({ title, message, indicator = "blue" }) => {
      frappe.msgprint({
        title,
        message,
        indicator,
      });
    };
    const refreshBOrders = async () => {
      items = [];
      selectedItems = [];
      await loadItems();
    };
    const loadItems = async () => {
      loading.value = true;
      error.value = null;

      try {
        if (props.filters.customer || props.filters.month ||props.filters.year) {
         
        
        const res = await api.getBlanketOrdersWithItems(props.filters);
        const data = res?.data?.message;

        if (!Array.isArray(data)) {
          throw new Error("Invalid response from server");
        }

        // if (!data.length) {
        //   showMessage({
        //     title: "No Data",
        //     message: "No pending items found for selected filters",
        //     indicator: "orange",
        //   });
        // }

        items.value = data;
      }else{
         items.value = [];
      }
      } catch (e) {
        error.value = e?.message || "Failed to load Blanket Order items";

        showMessage({
          title: "Load Failed",
          message: error.value,
          indicator: "red",
        });
      } finally {
        loading.value = false;
      }
    };

    const selectAll = () => {
      selectedItems.value = [...filteredItems.value];
    };

    const unselectAll = () => {
      selectedItems.value = [];
    };

    const createSalesOrder = async () => {
      if (!selectedItems.value.length) {
        showMessage({
          title: "No Selection",
          message: "Please select at least one item",
          indicator: "orange",
        });
        return;
      }

      const payload = selectedItems.value.map((item) => ({
        bo_name: item.bo_name,
        item_code: item.item_code,
        schedule_qty: Number(item.schedule_qty) || 0,
        rate: item.rate || 0,
        bom_no: item.bom_no || null,
        warehouse: item.warehouse || null,
      }));

      try {
        const res = await api.createSalesOrderFromBOItems(payload);
        const data = res?.data?.message;

        if (!data || data.status !== "success") {
          throw new Error("Unexpected server response");
        }

        let html = "";

        // ✅ Created
        if (data.created_sales_orders?.length) {
          html += `
        <p class="text-green-600">
          <b>Created Sales Orders:</b><br>
          ${data.created_sales_orders.join("<br>")}
        </p>
      `;
        }

        // ⚠️ Skipped
        if (data.skipped?.length) {
          html += `
        <hr>
        <p class="text-orange-600 mt-2">
          <b>Skipped:</b><br>
          ${data.skipped.map((s) => `BO: ${s.blanket_order} – ${s.reason}`).join("<br>")}
        </p>
      `;
        }

        showMessage({
          title: "Sales Order Creation Summary",
          message: html,
          indicator: data.skipped?.length ? "orange" : "green",
        });

        selectedItems.value = [];
        emit("update:selected", []);
      } catch (err) {
        // 🔥 Handles frappe.throw(), permission, DB errors
        showMessage({
          title: "Error",
          message: err?.response?.data?._server_messages
            ? JSON.parse(err.response.data._server_messages)
              .map((m) => JSON.parse(m).message)
              .join("<br>")
            : err.message || "Failed to create Sales Order",
          indicator: "red",
        });
      }
    };

    const validateScheduleQty = (item) => {
      if (item.schedule_qty == null) return;

      if (item.schedule_qty < 0) {
        item.schedule_qty = 0;
      }

      if (item.schedule_qty > item.remaining_bo_qty) {
        item.schedule_qty = item.remaining_bo_qty;

        showMessage({
          title: "Invalid Quantity",
          message: `Schedule Qty cannot exceed Pending Qty (${item.remaining_bo_qty})`,
          indicator: "orange",
        });
      }
    };



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
      refreshBOrders,
      validateScheduleQty,
    };
  },
};
</script>
