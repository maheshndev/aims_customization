<template>
  <div class="sales-orders rounded-xl shadow-sm p-2">
    <!-- Loading -->
    <div v-if="loading" class="text-gray-500 animate-pulse">Loading Sales Orders...</div>

    <!-- Error -->
    <div v-if="error" class="bg-red-100 text-red-700 px-4 py-2 border border-red-200 rounded mb-4">
      {{ error }}
    </div>

    <!-- ACTIONS -->
    <div v-if="orders.length && !loading" class="flex justify-end gap-3 mb-3">
      <button class="px-3 py-1 bg-blue-600 text-black rounded shadow" @click="selectAll">
        Select All
      </button>
      <button class="px-3 py-1 bg-gray-500 text-black rounded shadow" @click="unselectAll">
        Unselect All
      </button>
    </div>

    <!-- SALES ORDER TABLE -->
    <div v-if="orders.length && !loading" class="overflow-auto rounded-b-xl">
      <table class="min-w-[1200px] table-auto divide-y divide-gray-200 border">
        <thead class="bg-gray-100">
          <tr>
            <th class="px-3 py-2 border">
              <input type="checkbox" :checked="isAllSelected" @change="toggleSelectAll" />
            </th>
            <th class="px-3 py-2 border whitespace-nowrap">#</th>
            <th class="px-3 py-2 border whitespace-nowrap">SO ID</th>
            <th class="px-3 py-2 border whitespace-nowrap">Customer</th>
            <th class="px-3 py-2 border text-right whitespace-nowrap">Qty</th>
            <th class="px-3 py-2 border whitespace-nowrap">Month</th>
            <th class="px-3 py-2 border whitespace-nowrap">Transaction</th>
            <th class="px-3 py-2 border whitespace-nowrap">Delivery</th>
            <th class="px-3 py-2 border whitespace-nowrap">Status</th>
          </tr>
        </thead>

        <tbody class="divide-y divide-gray-200">
          <tr v-for="(so, index) in orders" :key="so.name" class="hover:bg-gray-50">
            <td class="border px-3 py-2">
              <input type="checkbox" :value="so.name" v-model="selectedLocal" />
            </td>
            <td class="border px-3 py-2 whitespace-nowrap">{{ index + 1 }}</td>
            <td class="border px-3 py-2 whitespace-nowrap">{{ so.name }}</td>
            <td class="border px-3 py-2 whitespace-nowrap">{{ so.customer_name }}</td>
            <td class="border px-3 py-2 text-right whitespace-nowrap">
              {{ so.total_qty }}
            </td>
            <td class="border px-3 py-2 whitespace-nowrap">{{ so.month }}</td>
            <td class="border px-3 py-2 whitespace-nowrap">
              {{ so.transaction_date }}
            </td>
            <td class="border px-3 py-2 whitespace-nowrap">{{ so.delivery_date }}</td>
            <td class="border px-3 py-2 whitespace-nowrap">{{ so.status }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- EMPTY STATE -->
    <div v-if="!orders.length && !loading" class="text-gray-500 text-center mt-4">
      No Sales Orders found.
    </div>

    <!-- FINISHED GOODS SECTION -->
    <div v-if="fgItems.length" class="mt-6 border-t pt-4 overflow-auto rounded-b-xl">
      <h3 class="font-bold text-lg mb-2">Finished Good Items (from selected SOs)</h3>
      <button class="px-3 py-1 bg-green-500 text-black rounded shadow hover:bg-green-600 m-1"
        @click="createMixPlannerBOM">
        Create Planner Mix BOM
      </button>

      <table class="min-w-[800px] table-auto divide-y divide-gray-200 border rounded-xl">
        <thead class="bg-gray-100">
          <tr>

            <th>Selected</th>
            <th class="px-3 py-2 border whitespace-nowrap">#</th>
            <th class="px-3 py-2 border whitespace-nowrap">Item Code</th>
            <th class="px-3 py-2 border whitespace-nowrap">Item Name</th>
            <th class="px-3 py-2 border text-right whitespace-nowrap">Qty</th>
            <th class="px-3 py-2 border text-right whitespace-nowrap">Item Group</th>
            <th class="px-3 py-2 border text-right whitespace-nowrap">Rate</th>
            <th class="px-3 py-2 border text-right whitespace-nowrap">BOM No</th>
          </tr>
        </thead>

        <tbody class="divide-y divide-gray-100">
          <tr v-for="(item, index) in fgItems" :key="item.item_code" class="hover:bg-gray-50">
            <td class="border px-3 py-2">
              <input type="checkbox" :value="item" v-model="selectedFGItems" />
            </td>
            <td class="border px-3 py-2 whitespace-nowrap">{{ index + 1 }}</td>
            <td class="border px-3 py-2 whitespace-nowrap">{{ item.item_code }}</td>
            <td class="border px-3 py-2 whitespace-nowrap">{{ item.item_name }}</td>
            <td class="border px-3 py-2 text-right whitespace-nowrap">
              {{ item.qty }}
            </td>
            <td class="border px-3 py-2 text-right whitespace-nowrap">
              {{ item.item_group }}
            </td>
            <td class="border px-3 py-2 text-right whitespace-nowrap">
              {{ item.rate }}
            </td>
             <td class="border px-3 py-2 text-right whitespace-nowrap">
              {{ item.bom_no }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed } from "vue";
import { api } from "../services/api";

const props = defineProps({
  boItems: { type: Array, default: () => [] },
  filters: { type: Object, required: true },
});

const emit = defineEmits(["update:selected", "fg-loaded", "so-loaded"]);

const loading = ref(false);
const error = ref(null);
const orders = ref([]);
const selectedLocal = ref([]);
const fgItems = ref([]);
const selectedFGItems = ref([]);

// ----------------------------------------------------
// ALL SELECTED CHECKBOX
// ----------------------------------------------------
const isAllSelected = computed(
  () => orders.value.length > 0 && selectedLocal.value.length === orders.value.length
);

// ----------------------------------------------------
// SELECT HANDLERS
// ----------------------------------------------------
const selectAll = () => {
  selectedLocal.value = orders.value.map((o) => o.name);
  processFGItems();
};

const unselectAll = () => {
  selectedLocal.value = [];
  fgItems.value = [];
  emit("fg-loaded", []);
};

const toggleSelectAll = () => (isAllSelected.value ? unselectAll() : selectAll());

// ----------------------------------------------------
// Collect FG items from selected Sales Orders
// ----------------------------------------------------
const processFGItems = () => {
  const selectedOrders = orders.value.filter((o) => selectedLocal.value.includes(o.name));

  const items = [];
  selectedOrders.forEach((o) => {
    (o.items || []).forEach((it) => items.push(it));
  });

  fgItems.value = items;

  emit("fg-loaded", items);
  emit("update:selected", selectedLocal.value);
};

// When checkbox changes
watch(selectedLocal, processFGItems);

const createMixPlannerBOM = () => {
  if (!selectedFGItems.value.length) {
    frappe.msgprint("Please select one Finished Good to create a Mix BOM.");
    return;
  }

  if (selectedFGItems.value.length > 1) {
    frappe.msgprint("Please select only ONE FG item to create a Mix BOM.");
    return;
  }

  const fgItem = selectedFGItems.value[0].item_code;
  const qty = selectedFGItems.value[0].qty || 1;
  const item_group = selectedFGItems.value[0].item_group || "";

  let bom_type = "";

  if (item_group === "Finish Good") {
    bom_type = "FG";
  } else if (item_group === "Semi Finish Good") {
    bom_type = "SFG";
  } else {
    bom_type = ""; // default or ignore
  }

  // Build URL with FG Item + Qty + Type
  const url = `/app/bom/new-bom` + `?item=${fgItem}` + `&bom_type=${bom_type}`;

  window.location.href = url;
};

// ----------------------------------------------------
// FETCH ORDERS WHEN FILTERS CHANGE
// ----------------------------------------------------
const fetchOrders = async () => {
  if (!props.filters) {
    return;
  }

  loading.value = true;
  error.value = null;

  try {


    if (props.filters.customer || props.filters.month || props.filters.year) {
      const res = await api.getSalesOrders(props.filters);

      orders.value = res.data.message || [];
      selectedLocal.value = [];
      fgItems.value = [];

      emit("so-loaded", orders.value);
    }
    else {
      orders.value = []
    }

  } catch (err) {
    console.error(err);
    error.value = "Failed to load Sales Orders.";
  } finally {
    loading.value = false;
  }
};

watch(() => [props.filters], fetchOrders, { immediate: true, deep: true });
</script>
