<template>
  <div class="sales-orders bg-white rounded-xl shadow-sm">

    <!-- Loading -->
    <div v-if="loading" class="text-gray-500 animate-pulse">
      Loading Sales Orders...
    </div>

    <!-- Error -->
    <div v-if="error" class="bg-red-100 text-red-700 px-4 py-2 border border-red-200 rounded mb-4">
      {{ error }}
    </div>

    <!-- Actions -->
    <div v-if="orders.length && !loading" class="flex justify-end gap-3 mb-3">
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
    <div v-if="orders.length && !loading" class="overflow-x-auto">
      <table class="min-w-full border border-gray-200 divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th class="px-3 py-2 text-left text-sm font-medium border w-10">
              <input type="checkbox" :checked="isAllSelected" @change="toggleSelectAll" />
            </th>
            <th class="px-3 py-2 text-left text-sm font-medium border">SO</th>
            <th class="px-3 py-2 text-left text-sm font-medium border">Customer</th>
            <th class="px-3 py-2 text-right text-sm font-medium border">Qty</th>
            <th class="px-3 py-2 text-right text-sm font-medium border">Month</th>
            <th class="px-3 py-2 text-right text-sm font-medium border">Transaction Date</th>
            <th class="px-3 py-2 text-left text-sm font-medium border">Delivery Date</th>
            <th class="px-3 py-2 text-left text-sm font-medium border">Status</th>
          </tr>
        </thead>

        <tbody class="divide-y divide-gray-100">
          <tr v-for="so in orders" :key="so.name" class="hover:bg-gray-50 transition">
            <td class="border px-3 py-2">
              <input type="checkbox" :value="so.name" v-model="selectedLocal" @change="handleSelectionChange" />
            </td>

            <td class="border px-3 py-2">{{ so.name }}</td>
            <td class="border px-3 py-2">{{ so.customer_name }}</td>
            <td class="border px-3 py-2 text-right">{{ so.total_qty }}</td>
            <td class="border px-3 py-2 text-right">{{ so.month }}</td>
            <td class="border px-3 py-2 text-right">{{ so.transaction_date }}</td>
            <td class="border px-3 py-2">{{ so.delivery_date }}</td>
            <td class="border px-3 py-2">{{ so.status }}</td>
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
