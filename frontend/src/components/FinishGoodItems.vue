<template>
  <div class="rounded shadow-sm p-4 bg-white">

    <!-- Loading -->
    <div v-if="loading" class="text-gray-500">
      Loading Finished Goods...
    </div>

    <!-- Error -->
    <div v-if="error" class="text-red-500 mb-2">
      {{ error }}
    </div>

    <!-- Table -->
    <div v-if="items.length && !loading" class="overflow-auto">
      <!-- Actions -->
      <div class="flex items-center gap-3 mb-3">
        <button
          class="px-3 py-1 bg-blue-600 text-black rounded hover:bg-blue-700"
          @click="selectAll"
        >
          Select All
        </button>

        <button
          class="px-3 py-1 bg-gray-600 text-black rounded hover:bg-gray-700"
          @click="unselectAll"
        >
          Unselect All
        </button>

        <span class="text-gray-600">
          Selected: {{ selectedItems.length }}
        </span>
      </div>

      <table class="min-w-[900px] table-auto border-collapse w-full">
        <thead class="bg-gray-100">
          <tr>
            
            <th class="border px-3 py-2 text-center">
              <input
                type="checkbox"
                :checked="isAllSelected"
                @change="toggleSelectAll"
              />
            </th>
            <th class="border px-3 py-2 text-center">#</th>
            <th class="border px-3 py-2 text-left">Sales Order</th>
            <th class="border px-3 py-2 text-left">Item Code</th>
            <th class="border px-3 py-2 text-left">Item Name</th>
            <th class="border px-3 py-2 text-right">Qty</th>
            <th class="border px-3 py-2 text-left">UOM</th>
          </tr>
        </thead>

        <tbody>
          <tr
            v-for="(it, index) in items"
            :key="`${it.sales_order}-${it.item_code}`"
            class="hover:bg-gray-50"
          >
          <td class="border px-3 py-2 text-center">
              <input
                type="checkbox"
                :value="it"
                v-model="selectedItems"
              />
            </td>
            <td class="border px-3 py-2 text-center">
              {{ index + 1 }}
            </td>
            
            <td class="border px-3 py-2">{{ it.sales_order }}</td>
            <td class="border px-3 py-2">{{ it.item_code }}</td>
            <td class="border px-3 py-2">{{ it.item_name }}</td>
            <td class="border px-3 py-2 text-right">{{ it.qty }}</td>
            <td class="border px-3 py-2">{{ it.uom }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- No Data -->
    <div v-if="!items.length && !loading" class="text-gray-500">
      No Finished Goods found.
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed } from "vue";
import { api } from "../services/api";

const props = defineProps({
  salesOrders: { type: Array, default: () => [] },
});

const emit = defineEmits(["update:selected"]);

const items = ref([]);
const selectedItems = ref([]);
const loading = ref(false);
const error = ref(null);

const isAllSelected = computed(
  () =>
    items.value.length &&
    selectedItems.value.length === items.value.length
);

// Fetch FG items
const fetchFinishGoods = async () => {
  if (!props.salesOrders.length) {
    items.value = [];
    selectedItems.value = [];
    emit("update:selected", []);
    return;
  }

  loading.value = true;
  error.value = null;

  try {
    const res = await api.getFinishGoodsFromSalesOrders(props.salesOrders);

    items.value =
      res?.data?.message?.filter(
        (i) => i.item_group === "Finished Goods"
      ) || [];

    selectedItems.value = [];
    emit("update:selected", []);
  } catch (err) {
    error.value = "Failed to fetch Finished Goods.";
  } finally {
    loading.value = false;
  }
};

// Selection helpers
function toggleSelectAll(e) {
  e.target.checked ? selectAll() : unselectAll();
}

function selectAll() {
  selectedItems.value = [...items.value];
}

function unselectAll() {
  selectedItems.value = [];
}

// Emit selection
watch(
  () => selectedItems.value,
  (val) => emit("update:selected", val),
  { deep: true }
);

// Watch sales orders
watch(
  () => props.salesOrders,
  fetchFinishGoods,
  { immediate: true, deep: true }
);
</script>
