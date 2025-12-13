<template>
  <div class="raw-materials  rounded shadow-sm p-4">

    <!-- Loading -->
    <div v-if="loading" class="text-gray-500">Loading Raw Materials...</div>

    <!-- Error -->
    <div v-if="error" class="text-red-500 mb-2">{{ error }}</div>

    <!-- Actions -->
    <div v-if="materials.length && !loading" class="flex justify-end gap-2 mb-3">
      <button class="px-3 py-1 bg-blue-600 text-black rounded m-1" @click="selectAll">Select All</button>
      <button class="px-3 py-1 bg-gray-500 text-black rounded m-1" @click="unselectAll">Unselect All</button>
    </div>

    <!-- Table -->
    <div v-if="materials.length && !loading" class="overflow-auto rounded-b-2xl">
      <table class="min-w-[1200px] table-auto border border-gray-200 divide-y divide-gray-200">
        <thead class="bg-gray-100">
          <tr>
            <th class="border px-3 py-2 w-10 text-left whitespace-nowrap">
              <input type="checkbox" :checked="isAllSelected" @change="toggleSelectAll" />
            </th>
             <th class="border px-3 py-2 text-left  whitespace-nowrap">#</th>
            <th class="border px-3 py-2 text-left  whitespace-nowrap">BOM</th>
            <th class="border px-3 py-2 text-left whitespace-nowrap">Material</th>
            <th class="border px-3 py-2 text-left whitespace-nowrap">Required Qty</th>
            <th class="border px-3 py-2 text-left whitespace-nowrap">Available Qty</th>
            <th class="border px-3 py-2 text-left whitespace-nowrap">Consumed Qty</th>
          </tr>
        </thead>

        <tbody>
          <tr v-for="(rm, index) in materials"  class="hover:bg-gray-50 transition">
            <td class="border px-3 py-2 text-center whitespace-nowrap">
              <input type="checkbox" v-model="selectedRows" :value="rm" :key="index"/>
            </td>
            <td class="border px-3 py-2 whitespace-nowrap">{{ index }}</td>
            <td class="border px-3 py-2 whitespace-nowrap">{{ rm.bom_no }}</td>
            <td class="border px-3 py-2 whitespace-nowrap">{{ rm.rm_item_name }}</td>
            <td class="border px-3 py-2 whitespace-nowrap">
              <input type="number"
                     v-model.number="rm.total_required_qty"
                     @input="emitUpdate"
                     class="w-full border px-2 py-1 rounded whitespace-nowrap" />
            </td>
            <td class="border px-3 py-2 whitespace-nowrap">{{ rm.available_qty }}</td>
            <td class="border px-3 py-2 whitespace-nowrap">{{ rm.consumed_qty }}</td>
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
const selectedRows = ref([]);
const loading = ref(false);
const error = ref(null);

// -----------------
// Select/Unselect All
// -----------------
const isAllSelected = computed(() => materials.value.length && selectedRows.value.length === materials.value.length);

const selectAll = () => { selectedRows.value = materials.value.map(m => m.rm_item_code); emitUpdate(); };
const unselectAll = () => { selectedRows.value = []; emitUpdate(); };
const toggleSelectAll = () => isAllSelected.value ? unselectAll() : selectAll();

// -----------------
// Fetch raw materials for selected BOMs
// -----------------
const fetchMaterials = async () => {
  if (!props.boms.length) {
    materials.value = [];
    selectedRows.value = [];
    emit("update:selected", []);
    emit("raw-material-loaded", []);
    return;
  }

  loading.value = true;
  error.value = null;

  try {
    const res = await api.getRawMaterialsForBOMs(props.boms);
    materials.value = res.data.message || [];
    selectedRows.value = materials.value.map(m => m.rm_item_code);
    emitUpdate();
  } catch (err) {
    console.error("Raw Material Fetch Error:", err);
    error.value = "Failed to fetch Raw Materials.";
  } finally {
    loading.value = false;
  }
};

// -----------------
// Emit updated selected rows & quantities
// -----------------
const emitUpdate = () => {
  const selected = materials.value.filter(m => selectedRows.value.includes(m.rm_item_code));
  emit("update:selected", selected);
  emit("raw-material-loaded", selected);
};

watch(() => props.boms, fetchMaterials, { deep: true, immediate: true });
</script>
