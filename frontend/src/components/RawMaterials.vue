<template>
  <div class="raw-materials bg-white rounded shadow-sm p-4">

    <!-- Loading -->
    <div v-if="loading" class="text-gray-500">Loading Raw Materials...</div>

    <!-- Error -->
    <div v-if="error" class="text-red-500 mb-2">{{ error }}</div>

    <!-- Actions -->
    <div v-if="materials.length && !loading" class="flex justify-end gap-2 mb-3">
      <button class="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700" @click="selectAll">
        Select All
      </button>
      <button class="px-3 py-1 bg-gray-500 text-white rounded hover:bg-gray-600" @click="unselectAll">
        Unselect All
      </button>
    </div>

    <!-- Table -->
    <div v-if="materials.length && !loading" class="overflow-x-auto">
      <table class="min-w-full border border-gray-200 divide-y divide-gray-200">
        <thead class="bg-gray-100">
          <tr>
            <th class="border px-3 py-2 w-10">
              <input type="checkbox" :checked="allSelected" @change="toggleSelectAll" />
            </th>
            <th class="border px-3 py-2 text-left">Item</th>
            <th class="border px-3 py-2 text-left">Material</th>
            <th class="border px-3 py-2 text-left">Required Qty</th>
            <th class="border px-3 py-2 text-left">Available Qty</th>
            <th class="border px-3 py-2 text-left">Consumed Qty</th>
          </tr>
        </thead>

        <tbody>
          <tr
            v-for="rm in materials"
            :key="rm.rm_item_code"
            class="hover:bg-gray-50 transition"
          >
            <td class="border px-3 py-2 text-center">
              <input type="checkbox" v-model="selectedMaterials" :value="rm.rm_item_code" />
            </td>
            <td class="border px-3 py-2">{{ rm.rm_item_code }}</td>
            <td class="border px-3 py-2">{{ rm.rm_item_name }}</td>
            <td class="border px-3 py-2">
              <input
                type="number"
                min="0"
                step="0.01"
                v-model.number="rm.total_required_qty"
                @input="emitSelected"
                class="w-full border rounded px-2 py-1"
              />
            </td>
            <td class="border px-3 py-2">{{ rm.available_qty }}</td>
            <td class="border px-3 py-2">{{ rm.consumed_qty }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- No Data -->
    <div v-if="!materials.length && !loading" class="text-gray-500 mt-2">
      No raw materials found.
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed } from "vue";
import { api } from "../services/api";

const props = defineProps({
  boms: { type: Array, default: () => [] },
  modelValue: { type: Array, default: () => [] } // v-model:selected
});

const emit = defineEmits(["update:selected", "raw-material-loaded"]);

const materials = ref([]);
const loading = ref(false);
const error = ref(null);
const selectedMaterials = ref([]);

// ---------------------------
// Computed for header checkbox
// ---------------------------
const allSelected = computed(() => {
  return materials.value.length > 0 && selectedMaterials.value.length === materials.value.length;
});

// ---------------------------
// Select/unselect helpers
// ---------------------------
const selectAll = () => {
  selectedMaterials.value = materials.value.map(m => m.rm_item_code);
  emitSelected();
};

const unselectAll = () => {
  selectedMaterials.value = [];
  emitSelected();
};

const toggleSelectAll = () => {
  allSelected.value ? unselectAll() : selectAll();
};

// ---------------------------
// Emit selected raw materials
// ---------------------------
const emitSelected = () => {
  const selectedRows = materials.value.filter(m => selectedMaterials.value.includes(m.rm_item_code));
  emit("update:selected", selectedRows);
  emit("raw-material-loaded", selectedRows);
};

// Watch selection changes
watch(selectedMaterials, emitSelected);

// ---------------------------
// Fetch raw materials for selected BOMs
// ---------------------------
const fetchMaterials = async () => {
  if (!props.boms.length) {
    materials.value = [];
    selectedMaterials.value = [];
    emitSelected();
    return;
  }

  loading.value = true;
  error.value = null;

  try {
    const res = await api.getRawMaterialsForBOMs(props.boms);
    materials.value = res.data.message || [];
    selectedMaterials.value = [];
    emitSelected();
  } catch (err) {
    console.error("Raw Material Fetch Error:", err);
    error.value = "Failed to fetch Raw Materials.";
  } finally {
    loading.value = false;
  }
};

// Watch selected BOMs and fetch raw materials automatically
watch(
  () => props.boms,
  () => fetchMaterials(),
  { deep: true, immediate: true }
);
</script>
