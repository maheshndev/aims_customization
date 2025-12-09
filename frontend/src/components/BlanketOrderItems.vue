<template>
  <div class="blanket-order-items bg-white rounded-xl shadow-sm p-5">

    <!-- Selected BO Info -->
    <div class="flex justify-between items-center mb-4">
      <div v-if="selectedBoNames.length" class="text-sm text-gray-700">
        Selected BO(s): <span>{{ selectedBoNames.join(", ") }}</span>
      </div>
    </div>

    <!-- Top Controls -->
    <div class="flex justify-between items-center mb-3">
      <div v-if="items.length" class="flex items-center gap-2">
        <input type="checkbox" class="w-4 h-4" :checked="isAllSelected" @change="toggleSelectAll" />
        <label class="text-sm text-gray-700">Select All</label>
        <span class="text-xs text-gray-500 ml-2">{{ selectedItems.length }} selected</span>
      </div>

      <button v-if="selectedItems.length" @click="createSalesOrder"
        class="px-4 py-2 bg-black text-white rounded-lg hover:bg-gray-800 transition">
        Create Sales Orders
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="text-gray-500 animate-pulse py-4 text-center">
      Loading Finished Good Items...
    </div>

    <!-- Error -->
    <div v-if="error" class="bg-red-100 text-red-700 px-4 py-2 border border-red-200 rounded mb-4">
      {{ error }}
    </div>

    <!-- Items Table -->
    <div v-if="items.length && !loading" class="overflow-x-auto">
      <table class="min-w-[1600px] border border-gray-200 divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th class="px-3 py-2 text-center border w-12">
              <input type="checkbox" :checked="isAllSelected" @change="toggleSelectAll" />
            </th>
            <th v-for="h in headers" :key="h" class="px-3 py-2 text-left text-sm font-medium text-gray-700 border">
              {{ h }}
            </th>
          </tr>
        </thead>

        <tbody class="divide-y divide-gray-100">
          <tr v-for="item in items" :key="item.item_code" class="hover:bg-gray-50 transition">
            <td class="px-3 py-2 text-center border">
              <input type="checkbox" class="w-4 h-4" :value="item" v-model="selectedItems" />
            </td>
            <td v-for="key in fieldKeys" :key="key" class="px-3 py-2 text-sm border text-gray-800">
              {{ item[key] }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- No Items -->
    <div v-if="selectedBoNames.length && !items.length && !loading" class="text-gray-500 mt-4 text-center">
      No Finished Goods items found for the selected Blanket Orders.
    </div>
  </div>
</template>

<script>
import { api } from "../services/api";

export default {
  name: "BlanketOrderItems",

  props: {
    selectedBoNames: { type: Array, default: () => [] },
    selected: { type: Array, default: () => [] }, // v-model for selected items
  },

  data() {
    return {
      items: [],
      selectedItems: [],
      loading: false,
      error: null,

      headers: [
        "Item Code",
        "Item Name",
        "Order Qty",
        "Rate",
        "Available Stock",
        "Produced Stock",
        "WIP Stock",
        "Balance Produce",
        "Balance Deliver",
      ],

      fieldKeys: [
        "item_code",
        "item_name",
        "order_qty",
        "rate",
        "available_stock_nos",
        "produced_stock_nos",
        "wip_stock_nos",
        "balance_to_produce_qty",
        "balance_to_deliver_qty",
      ],
    };
  },

  watch: {
    selectedBoNames: {
      immediate: true,
      handler(list) {
        if (list?.length) this.loadItems(list);
        else {
          this.items = [];
          this.selectedItems = [];
        }
      },
    },
  },

  computed: {
    isAllSelected() {
      return this.items.length && this.selectedItems.length === this.items.length;
    },
  },

  methods: {
    async loadItems(boNames) {
      this.loading = true;
      this.error = null;

      try {
        const res = await api.getBlanketOrderItems({ bo_list: boNames });
        this.items = res.data.message || [];
		console.log("Fetched BO items:", boNames, this.items);
      } catch {
        this.error = 'Failed to load Blanket Order items.';
      } finally {
        this.loading = false;
      }
    },

    toggleSelectAll(e) {
      if (e.target.checked) this.selectedItems = [...this.items];
      else this.selectedItems = [];
    },

    async createSalesOrder() {
      if (!this.selectedItems.length) return;

      try {
        await api.createSalesOrderFromBOItems(this.selectedItems);
        frappe.msgprint({ title: "Success", message: "Sales Order created.", indicator: "green" });
        this.selectedItems = [];
      } catch {
        frappe.msgprint({ title: "Error", message: "Failed to create Sales Order.", indicator: "red" });
      }
    },
  },
};
</script>
