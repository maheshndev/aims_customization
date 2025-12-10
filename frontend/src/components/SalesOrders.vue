<template>
  <div class="sales-orders rounded-xl shadow-sm p-2">

    <!-- Loading -->
    <div v-if="loading" class="text-gray-500 animate-pulse">
      Loading Sales Orders...
    </div>

    <!-- Error -->
    <div v-if="error" class="bg-red-100 text-red-700 px-4 py-2 border border-red-200 rounded mb-4">
      {{ error }}
    </div>

    <!-- Actions -->
    <div v-if="orders.length && !loading" class="flex justify-end items-center gap-3 mb-3">
      <button class="px-3 py-1 m-1 bg-blue-600 text-black rounded shadow hover:bg-blue-700" @click="selectAll">
        Select All
      </button>

      <button class="px-3 py-1 m-1 bg-gray-500 text-black rounded shadow hover:bg-gray-600" @click="unselectAll">
        Unselect All
      </button>
       <button class="px-3 py-1 m-1 bg-gray-500 text-black rounded shadow hover:bg-gray-600" @click="unselectAll">
       Create / Schedule Work Order
      </button>
    </div>

    <!-- Sales Orders Table -->
    <div v-if="orders.length && !loading" class="overflow-auto rounded-b-2xl">
      <table class="min-w-[1200px] table-auto border border-gray-200 divide-y divide-gray-200">
        <thead class="bg-gray-100 sticky">
          <tr>
            <th class="px-3 py-2 text-left text-sm font-medium border w-10">
              <input type="checkbox" :checked="isAllSelected" @change="toggleSelectAll" />
            </th>
            <th class="px-3 py-2 text-left text-sm font-medium border whitespace-nowrap">SO</th>
            <th class="px-3 py-2 text-left text-sm font-medium border whitespace-nowrap">Customer</th>
            <th class="px-3 py-2 text-right text-sm font-medium border whitespace-nowrap">Qty</th>
            <th class="px-3 py-2 text-right text-sm font-medium border whitespace-nowrap">Month</th>
            <th class="px-3 py-2 text-right text-sm font-medium border whitespace-nowrap">Transaction Date</th>
            <th class="px-3 py-2 text-left text-sm font-medium border whitespace-nowrap">Delivery Date</th>
            <th class="px-3 py-2 text-left text-sm font-medium border whitespace-nowrap">Status</th>
          </tr>
        </thead>

        <tbody class="divide-y divide-gray-100">
          <tr v-for="so in orders" :key="so.name" class="hover:bg-gray-50 transition">
            <td class="border px-3 py-2">
              <input type="checkbox" :value="so.name" v-model="selectedLocal" @change="handleSelectionChange" />
            </td>

            <td class="border px-3 py-2 whitespace-nowrap">{{ so.name }}</td>
            <td class="border px-3 py-2 whitespace-nowrap">{{ so.customer_name }}</td>
            <td class="border px-3 py-2 text-right whitespace-nowrap">{{ so.total_qty }}</td>
            <td class="border px-3 py-2 text-right whitespace-nowrap">{{ so.month }}</td>
            <td class="border px-3 py-2 text-right whitespace-nowrap">{{ so.transaction_date }}</td>
            <td class="border px-3 py-2 whitespace-nowrap">{{ so.delivery_date }}</td>
            <td class="border px-3 py-2 whitespace-nowrap">{{ so.status }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- No Data -->
    <div v-if="!orders.length && !loading" class="text-gray-500 mt-4 text-center">
      No Sales Orders found.
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed } from "vue";
import { api } from "../services/api";

const props = defineProps({
  items: { type: Array, default: () => [] },
  customer: { type: String, default: "" },
  selected: { type: Array, default: () => [] },
});

const emit = defineEmits([
  "so-loaded",
  "boms-loaded",
  "update:selected",
]);

const loading = ref(false);
const error = ref(null);
const orders = ref([]);

const selectedLocal = ref([]);

const isAllSelected = computed(() => {
  return (
    orders.value.length > 0 &&
    selectedLocal.value.length === orders.value.length
  );
});

// ---------------------
// SELECT HANDLERS
// ---------------------

const emitSelected = () => {
  emit("update:selected", [...selectedLocal.value]);
};

const selectAll = () => {
  selectedLocal.value = orders.value.map((so) => so.name);
  handleSelectionChange();
};

const unselectAll = () => {
  selectedLocal.value = [];
  handleSelectionChange();
};

const toggleSelectAll = () => {
  isAllSelected.value ? unselectAll() : selectAll();
};

// When selection changes → fetch BOMs
const handleSelectionChange = async () => {
  emitSelected();

  if (!selectedLocal.value.length) {
    emit("boms-loaded", []);
    return;
  }

  try {
    const res = await api.getBOMsForSalesOrder(selectedLocal.value);
    emit("boms-loaded", res.data.message || []);
  } catch (e) {
    console.error("Error loading BOMs:", e);
    emit("boms-loaded", []);
  }
};

// ---------------------
// FETCH SALES ORDERS
// ---------------------
const fetchOrders = async () => {
  loading.value = true;
  error.value = null;

  try {
    const res = await api.getSalesOrders({
      customer: props.customer || "",
      items: props.items || [],
    });

    orders.value = res.data.message || [];

    selectedLocal.value = [];
    emit("so-loaded", orders.value);

    // emit("boms-loaded", []); // reset BOMs

  } catch (err) {
    console.error("SO Fetch Error:", err);
    error.value = "Failed to fetch Sales Orders.";
  } finally {
    loading.value = false;
  }
};

watch(
  () => [props.items, props.customer],
  () => fetchOrders(),
  { immediate: true, deep: true }
);
</script>
