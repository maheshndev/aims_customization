<template>
  <div class="work-orders rounded shadow-sm p-4">

    <!-- Loading -->
    <div v-if="loading" class="text-gray-500">Loading Work Orders...</div>

    <!-- Error -->
    <div v-if="error" class="text-red-500 mb-2">{{ error }}</div>

    <!-- Table -->
    <div v-if="workOrders.length" class="overflow-auto rounded-b-2xl">

      <!-- Actions -->
      <div class="flex items-center gap-3 mb-3">
        <button class="px-3 py-1 bg-blue-600 text-black rounded hover:bg-blue-700 m-1" @click="selectAll">
          Select All
        </button>

        <button class="px-3 py-1 bg-gray-600 text-black rounded hover:bg-gray-700 m-1" @click="unselectAll">
          Unselect All
        </button>

        <span class="text-gray-600 m-1">
          Selected: {{ selectedWorkOrders.length }}
        </span>
      </div>

      <table class="min-w-[1200px] table-auto w-full border-collapse">
        <thead class="bg-gray-100">
          <tr>
            <th class="border px-3 py-2 text-left">
              <input type="checkbox" :checked="isAllSelected" @change="toggleSelectAll" />
            </th>

            <th class="border px-3 py-2 text-left whitespace-nowrap">WO</th>
            <th class="border px-3 py-2 text-left whitespace-nowrap">SO</th>
            <th class="border px-3 py-2 text-left whitespace-nowrap">Item</th>
            <th class="border px-3 py-2 text-left whitespace-nowrap">Qty</th>
            <th class="border px-3 py-2 text-left whitespace-nowrap">Produced Qty</th>
            <th class="border px-3 py-2 text-left whitespace-nowrap">Planned Start Date</th>
            <th class="border px-3 py-2 text-left whitespace-nowrap">Planned End Date</th>
            <th class="border px-3 py-2 text-left whitespace-nowrap">Status</th>
            <th class="border px-3 py-2 text-left whitespace-nowrap">Expected Delivery Date</th>
            <th class="border px-3 py-2 text-left whitespace-nowrap">Stock UOM</th>
            <th class="border px-3 py-2 text-left whitespace-nowrap">Material Transferred</th>
            <th class="border px-3 py-2 text-left whitespace-nowrap">Disassembled Qty</th>
            <th class="border px-3 py-2 text-left whitespace-nowrap">BOM No</th>
            <th class="border px-3 py-2 text-left whitespace-nowrap">FG Warehouse</th>
            <th class="border px-3 py-2 text-left whitespace-nowrap">Scrap Warehouse</th>
            <th class="border px-3 py-2 text-left whitespace-nowrap">WIP Warehouse</th>
            <th class="border px-3 py-2 text-left whitespace-nowrap">Company</th>
          </tr>
        </thead>

        <tbody>
          <tr v-for="wo in workOrders" :key="wo.name" class="hover:bg-gray-50">
            <td class="border px-3 py-2 text-center">
              <input
                type="checkbox"
                :value="wo.name"
                v-model="selectedWorkOrders"
                @change="emitSelection"
              />
            </td>

            <td class="border px-3 py-2 whitespace-nowrap">{{ wo.wo_name }}</td>
            <td class="border px-3 py-2 whitespace-nowrap">{{ wo.so_name }}</td>
            <td class="border px-3 py-2 whitespace-nowrap">{{ wo.production_item }}</td>
            <td class="border px-3 py-2 whitespace-nowrap">{{ wo.wo_qty }}</td>
            <td class="border px-3 py-2 whitespace-nowrap">{{ wo.produced_qty }}</td>
            <td class="border px-3 py-2 whitespace-nowrap">{{ wo.planned_start_date }}</td>
            <td class="border px-3 py-2 whitespace-nowrap">{{ wo.planned_end_date }}</td>
            <td class="border px-3 py-2 whitespace-nowrap">{{ wo.status }}</td>
            <td class="border px-3 py-2 whitespace-nowrap">{{ wo.expected_delivery_date }}</td>
            <td class="border px-3 py-2 whitespace-nowrap">{{ wo.stock_uom }}</td>
            <td class="border px-3 py-2 whitespace-nowrap">{{ wo.material_transferred_for_manufacturing }}</td>
            <td class="border px-3 py-2 whitespace-nowrap">{{ wo.disassembled_qty }}</td>
            <td class="border px-3 py-2 whitespace-nowrap">{{ wo.bom_no }}</td>
            <td class="border px-3 py-2 whitespace-nowrap">{{ wo.fg_warehouse }}</td>
            <td class="border px-3 py-2 whitespace-nowrap">{{ wo.scrap_warehouse }}</td>
            <td class="border px-3 py-2 whitespace-nowrap">{{ wo.wip_warehouse }}</td>
            <td class="border px-3 py-2 whitespace-nowrap">{{ wo.company }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- No Data -->
    <div v-if="!workOrders.length && !loading" class="text-gray-500 mt-2">
      No Work Orders found.
    </div>

  </div>
</template>

<script setup>
import { ref, computed, watch } from "vue";
import { api } from "../services/api";

const props = defineProps({
  salesOrders: { type: Array, default: () => [] },
});

const emit = defineEmits(["update:selected", "wo-loaded"]);

const workOrders = ref([]);
const selectedWorkOrders = ref([]);
const loading = ref(false);
const error = ref(null);

const isAllSelected = computed(() =>
  workOrders.value.length &&
  selectedWorkOrders.value.length === workOrders.value.length
);

// Fetch work orders
async function fetchWorkOrders() {
  if (!props.salesOrders.length) {
    workOrders.value = [];
    selectedWorkOrders.value = [];
    emitSelection();
    return;
  }

  loading.value = true;
  error.value = null;

  try {
    const res = await api.getWorkOrders(props.salesOrders);
    workOrders.value = res.data.message || [];
    
    
    selectedWorkOrders.value = []; // reset
    emitSelection();
    emit("wo-loaded", workOrders.value);

  } catch (err) {
    error.value = "Failed to fetch Work Orders.";
  } finally {
    loading.value = false;
  }
}

// Selections
function toggleSelectAll(e) {
  e.target.checked ? selectAll() : unselectAll();
}

function selectAll() {
  selectedWorkOrders.value = workOrders.value.map(wo => wo.name);
  emitSelection();
}

function unselectAll() {
  selectedWorkOrders.value = [];
  emitSelection();
}

function emitSelection() {
  emit("update:selected", [...selectedWorkOrders.value]);
}

// Watcher
watch(
  () => props.salesOrders,
  () => fetchWorkOrders(),
  { immediate: true, deep: true }
);
</script>
