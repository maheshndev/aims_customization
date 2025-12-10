<template>
  <div class="bom-list bg-white rounded-xl shadow-sm p-5">

    <!-- Loading -->
    <div v-if="loading" class="text-gray-500 animate-pulse">
      Loading BOMs...
    </div>

    <!-- Error -->
    <div v-if="error" class="bg-red-100 text-red-700 px-4 py-2 border border-red-200 rounded mb-4">
      {{ error }}
    </div>

    <!-- Actions -->
    <div v-if="filteredBOMs.length && !loading" class="flex justify-between items-center mb-3">

      <!-- Search -->
      <input v-model="search" type="text" placeholder="Search BOM / Item..."
        class="border px-3 py-1 rounded w-60 text-sm" />

      <div class="flex gap-3">
        <button class="px-3 py-1 bg-blue-600 text-white rounded shadow hover:bg-blue-700" @click="selectAll">
          Select All
        </button>
        <button class="px-3 py-1 bg-gray-500 text-white rounded shadow hover:bg-gray-600" @click="unselectAll">
          Unselect All
        </button>
        <button class="px-3 py-1 bg-green-500 text-white rounded shadow hover:bg-green-600"
          @click="createMixPlannerBOM">
          Create Planner Mix BOM
        </button>
        <button v-if="selectedLocal.length >= 2" @click="$emit('open-compare')"
          class="px-3 py-1 bg-purple-600 text-white rounded hover:bg-purple-700">
          Compare BOMs
        </button>

      </div>
    </div>

    <!-- BOM Table -->
    <div v-if="filteredBOMs.length && !loading" class="overflow-x-auto border rounded">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th class="px-3 py-2 border w-10 text-left">
              <input type="checkbox" :checked="isAllSelected" @change="toggleSelectAll" />
            </th>
            <th class="px-3 py-2 border text-left">Item</th>
            <th class="px-3 py-2 border text-left">BOM</th>
            <th class="px-3 py-2 border text-left">Qty</th>
            <th class="px-3 py-2 border text-left">BOM Type</th>
            <th class="px-3 py-2 border text-left">Required Qty</th>
            <th class="px-3 py-2 border text-left">Cavity</th>
            <th class="px-3 py-2 border text-left">PCS wt</th>
            <th class="px-3 py-2 border text-left">Runner wt</th>
            <th class="px-3 py-2 border text-left">Shot wt</th>
            <th class="px-3 py-2 border text-left">Gross wt</th>
            <th class="px-3 py-2 border text-left">Cycle Time</th>
            <th class="px-3 py-2 border text-left">UOM</th>
          </tr>
        </thead>

        <tbody class="divide-y divide-gray-100">
          <tr v-for="bom in filteredBOMs" :key="bom.bom_no" class="hover:bg-gray-50 transition">
            <td class="border px-3 py-2">
              <input type="checkbox" :value="bom.bom_no" v-model="selectedLocal" />
            </td>
            <td class="border px-3 py-2">{{ bom.item_code }}</td>
            <td class="border px-3 py-2">{{ bom.bom_no }}</td>
            <td class="border px-3 py-2">{{ bom.bom_qty }}</td>
            <td class="border px-3 py-2">{{ bom.bom_type }}</td>
            <td class="border px-3 py-2">{{ bom.required_for_selected_qty }}</td>
            <td class="border px-3 py-2">{{ bom.cavity }}</td>
            <td class="border px-3 py-2">{{ bom.pcs_wt }}</td>
            <td class="border px-3 py-2">{{ bom.runner_wt }}</td>
            <td class="border px-3 py-2">{{ bom.shot_wt }}</td>
            <td class="border px-3 py-2">{{ bom.gross_wt }}</td>
            <td class="border px-3 py-2">{{ bom.cycle_time }}</td>
            <td class="border px-3 py-2">{{ bom.uom }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Empty state -->
    <div v-if="!filteredBOMs.length && !loading" class="text-gray-500 text-center mt-4">
      No BOMs found.
    </div>

  </div>
</template>

<script setup>
import { ref, watch, computed } from "vue";
import { api } from "../services/api";

const props = defineProps({
  salesOrders: { type: Array, default: () => [] },
  selected: { type: Array, default: () => [] }, // v-model:selected
});

const emit = defineEmits(["update:selected", "bom-loaded"]);

const boms = ref([]);
const loading = ref(false);
const error = ref(null);

const selectedLocal = ref([]);

const search = ref("");

// ---------------------------------------------------
// Computed: Filter BOMs
// ---------------------------------------------------
const filteredBOMs = computed(() => {
  if (!search.value.trim()) return boms.value;

  const s = search.value.toLowerCase();

  return boms.value.filter(
    (b) =>
      b.bom_no.toLowerCase().includes(s) ||
      b.item_code.toLowerCase().includes(s)
  );
});

// ---------------------------------------------------
// Header checkbox
// ---------------------------------------------------
const isAllSelected = computed(() => {
  return (
    filteredBOMs.value.length > 0 &&
    selectedLocal.value.length === filteredBOMs.value.length
  );
});

// ---------------------------------------------------
// Watch Local Selection → Emit to parent
// ---------------------------------------------------
watch(selectedLocal, () => {
  emit("update:selected", [...selectedLocal.value]);

  const selectedObjects = boms.value.filter((b) =>
    selectedLocal.value.includes(b.bom_no)
  );

  emit("bom-loaded", selectedObjects);
});

// ---------------------------------------------------
// Select / Unselect
// ---------------------------------------------------
const selectAll = () => {
  selectedLocal.value = filteredBOMs.value.map((b) => b.bom_no);
};

const unselectAll = () => {
  selectedLocal.value = [];
};

const toggleSelectAll = () => {
  isAllSelected.value ? unselectAll() : selectAll();
};

const createMixPlannerBOM = () => {
  // Same as "Select All"
  selectAll();
};

// ---------------------------------------------------
// Fetch BOMs for selected SOs
// ---------------------------------------------------
const fetchBOMs = async () => {
  if (!props.salesOrders.length) {
    boms.value = [];
    selectedLocal.value = [];
    emit("bom-loaded", []);
    emit("update:selected", []);
    return;
  }

  loading.value = true;
  search.value = "";
  error.value = null;

  try {
    const res = await api.getBOMsForSalesOrder(props.salesOrders);
    boms.value = res.data.message || [];
    selectedLocal.value = [];

    emit("bom-loaded", []);
    emit("update:selected", []);
  } catch (err) {
    console.error(err);
    error.value = "Failed to fetch BOMs.";
  } finally {
    loading.value = false;
  }
};

watch(() => props.salesOrders, fetchBOMs, { deep: true, immediate: true });
</script>
