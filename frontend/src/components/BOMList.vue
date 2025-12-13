<template>
  <div class="bom-list rounded-xl shadow-sm p-2">

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

      <div class="flex gap-3">
        <button class="px-3 py-1 bg-blue-600 text-black rounded shadow hover:bg-blue-700 m-1" @click="selectAll">
          Select All
        </button>
        <button class="px-3 py-1 bg-gray-500 text-black rounded shadow hover:bg-gray-600 m-1" @click="unselectAll">
          Unselect All
        </button>
        <button v-if="selectedLocal.length >= 2" @click="$emit('open-compare')"
          class="px-3 py-1 bg-purple-600 text-black rounded hover:bg-purple-700 m-1">
          Compare BOMs
        </button>

         

      </div>
    </div>

    <!-- BOM Table -->
    <div v-if="filteredBOMs.length && !loading" class="overflow-auto rounded-b-2xl ">
      <table class="min-w-[1200px] table-auto divide-y divide-gray-200">
        <thead class="bg-gray-100 sticky">
          <tr>
            <th class="px-3 py-2 border w-10 text-left">
              <input type="checkbox" :checked="isAllSelected" @change="toggleSelectAll" />
            </th>
            <th class="px-3 py-2 border text-left whitespace-nowrap">#</th>
            <th class="px-3 py-2 border text-left whitespace-nowrap">Sales Order</th>
            <th class="px-3 py-2 border text-left whitespace-nowrap">BOM</th>
            <th class="px-3 py-2 border text-left whitespace-nowrap">Finish Good Item</th>
            <th class="px-3 py-2 border text-left whitespace-nowrap">Qty</th>
            <th class="px-3 py-2 border text-left whitespace-nowrap">BOM Type</th>
            <th class="px-3 py-2 border text-left whitespace-nowrap">Required Qty</th>
            <th class="px-3 py-2 border text-left whitespace-nowrap">Cavity</th>
            <th class="px-3 py-2 border text-left whitespace-nowrap">PCS wt</th>
            <th class="px-3 py-2 border text-left whitespace-nowrap">Runner wt</th>
            <th class="px-3 py-2 border text-left whitespace-nowrap">Shot wt</th>
            <th class="px-3 py-2 border text-left whitespace-nowrap">Gross wt</th>
            <th class="px-3 py-2 border text-left whitespace-nowrap">Cycle Time</th>
            <th class="px-3 py-2 border text-left whitespace-nowrap">Workstation / Machine</th>
            <th class="px-3 py-2 border text-left whitespace-nowrap">Moulds</th>

          </tr>
        </thead>

        <tbody class="divide-y divide-gray-100">
          <tr v-for="(bom, index) in filteredBOMs"  class="hover:bg-gray-50 transition">
            <td class="border px-3 py-2">
              <input type="checkbox" :value="bom.bom_no" :key="index" v-model="selectedLocal" />
            </td>
            <td class="border px-3 py-2 whitespace-nowrap">{{ index+1 }}</td>
            <td class="border px-3 py-2 whitespace-nowrap">{{ bom.sales_order }}</td>
            <td class="border px-3 py-2 whitespace-nowrap">{{ bom.bom_no || "No BOM Available" }}</td>
            <td class="border px-3 py-2 whitespace-nowrap">{{ bom.item_code }}</td>
            <td class="border px-3 py-2 whitespace-nowrap">{{ bom.bom_qty }}</td>
            <td class="border px-3 py-2 whitespace-nowrap">{{ bom.bom_type }}</td>
            <td class="border px-3 py-2 whitespace-nowrap">{{ bom.required_for_selected_qty }}</td>
            <td class="border px-3 py-2 whitespace-nowrap">{{ bom.cavity }}</td>
            <td class="border px-3 py-2 whitespace-nowrap">{{ bom.pcs_wt }}</td>
            <td class="border px-3 py-2 whitespace-nowrap">{{ bom.runner_wt }}</td>
            <td class="border px-3 py-2 whitespace-nowrap">{{ bom.shot_wt }}</td>
            <td class="border px-3 py-2 whitespace-nowrap">{{ bom.gross_wt }}</td>
            <td class="border px-3 py-2 whitespace-nowrap">{{ bom.cycle_time }}</td>
            <td class="border px-3 py-2 whitespace-nowrap">
              <select v-model="bom.selected_workstation" class="border rounded px-2 py-1">
                <option v-for="op in bom.bom_operations" :key="op.name" :value="op.workstation">
                  {{ op.workstation }}
                </option>
              </select>
            </td>
            <td class="border px-3 py-2 whitespace-nowrap">
              <select v-model="bom.selected_moulds" class="border rounded px-2 py-1">
                <option v-for="mould in bom.selected_moulds" :key="mould.mould_no" :value="mould.mould_no">
                  {{ mould.mould_no }} : {{ mould.mould_name }}
                </option>
              </select>
            </td>
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
  const selectedObjects = boms.value.filter((b) =>
    selectedLocal.value.includes(b.bom_no)
  );

  emit("update:selected", selectedLocal.value); // selected BOM numbers
  emit("update:capBOMs", selectedObjects);     // full objects including operations
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
    boms.value = (res.data.message || []).map(b => ({
      ...b,
      selected_workstation:
        b.bom_operations?.length ? b.bom_operations[0].workstation : null,
      selected_moulds:
        b.moulds?.length ? b.moulds[0].mould_name : null
    }));
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
