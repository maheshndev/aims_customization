<template>
  <div class="bom-list rounded-xl shadow-sm p-2 bg-white border border-gray-100">
    <div v-if="loading" class="text-gray-500 animate-pulse p-4 text-center">Loading BOMs...</div>

    <div v-if="error" class="bg-red-100 text-red-700 px-4 py-2 border border-red-200 rounded mb-4">
      {{ error }}
    </div>

    <div v-if="filteredBOMs.length && !loading" class="flex justify-between items-center mb-3">
      <div class="flex gap-2">
        <button class="px-2 py-1 bg-blue-50 text-blue-700 font-medium rounded hover:bg-blue-100 transition shadow-sm"
          @click="selectAll">
          Select All
        </button>
        <button class="px-2 py-1 bg-gray-50 text-gray-700 font-medium rounded hover:bg-gray-100 transition shadow-sm"
          @click="unselectAll">
          Unselect All
        </button>
        <button v-if="selectedLocal.length >= 2" @click="$emit('open-compare')"
          class="px-2 py-1 bg-purple-50 text-purple-700 font-medium rounded hover:bg-purple-200 transition shadow-sm">
          Compare BOMs ({{ selectedLocal.length }})
        </button>
      </div>
      <div class="text-xs text-gray-500 font-medium">
        {{ selectedLocal.length }} items selected
      </div>
    </div>

    <div v-if="filteredBOMs.length && !loading" class="overflow-auto rounded-xl border border-gray-200 shadow-sm">
      <table class="min-w-full table-auto divide-y divide-gray-200 text-sm">
        <thead class="bg-gray-50 uppercase">
          <tr>
            <th class="px-2 py-2 border text-left w-10 whitespace-nowrap">
              <input type="checkbox" :checked="isAllSelected" @change="toggleSelectAll"
                class="rounded border-gray-300" />
            </th>
            <th v-for="h in headers" :key="h"
              class="px-2 py-2 border border text-left font-semibold text-gray-600 whitespace-nowrap">
              {{ h }}
            </th>
          </tr>
        </thead>

        <tbody class="divide-y divide-gray-200 bg-white">
          <tr v-for="(bom, index) in filteredBOMs" :key="bom.row_uid" class="transition-colors duration-150"
            :class="selectedLocal.includes(bom) ? 'bg-blue-50/50' : 'hover:bg-gray-50'">

            <td class="px-2 py-2 text-center  whitespace-nowrap">
              <input type="checkbox" :value="bom" v-model="selectedLocal" class="rounded border-gray-300 shadow-sm" />
            </td>
            <td class="px-2 py-2 border text-gray-500 whitespace-nowrap">{{ index + 1 }}</td>
            <td class="px-2 py-2 border font-medium whitespace-nowrap">{{ bom.sales_order }}</td>
            <td class="px-2 py-2 border text-blue-600 font-medium whitespace-nowrap">{{ bom.bom_no || "No BOM Available"
              }}</td>
            <td class="px-2 py-2 border whitespace-nowrap relative group cursor-pointer">{{ bom.item_code }}
              <!-- Tooltip -->
              <div
                class="absolute left-1/2 transform -translate-x-1/2 -top-8 bg-gray-800 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap">
                {{ bom.item_name }}
              </div>
            </td>
            <td class="px-2 py-2 border whitespace-nowrap">{{ bom.bom_qty }}</td>
            <td class="px-2 py-2 border text-xs whitespace-nowrap"><span class="px-2 py-1 bg-gray-100 rounded-full">{{
              bom.bom_type }}</span></td>
            <td class="px-2 py-2 border whitespace-nowrap">{{ bom.customer }}</td>
            <td class="px-2 py-2 border font-bold text-gray-800 whitespace-nowrap">{{ bom.required_for_selected_qty }}
            </td>
            <td class="px-2 py-2 border font-bold text-orange-600 whitespace-nowrap">{{ bom.cavity }}</td>
            <td class="px-2 py-2 border whitespace-nowrap">{{ bom.pcs_wt }}</td>
            <td class="px-2 py-2 border whitespace-nowrap">{{ bom.runner_wt }}</td>
            <td class="px-2 py-2 border whitespace-nowrap">{{ bom.shot_wt }}</td>
            <td class="px-2 py-2 border font-medium whitespace-nowrap">{{ bom.gross_wt }}</td>
            <td class="px-2 py-2 border whitespace-nowrap">{{ bom.cycle_time }}s</td>

            <td class="px-2 py-2 border min-w-[180px] whitespace-nowrap">
              <select v-model="bom.selected_workstation"
                class="w-full text-xs border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500">
                <option disabled value="">Select Workstation</option>
                <option v-for="op in bom.bom_operations" :key="op.workstation" :value="op.workstation">
                  {{ op.workstation }}
                </option>
              </select>
            </td>
            <td class="px-2 py-2 min-w-[200px] whitespace-nowrap">
              <select v-model="bom.selected_mould"
                class="w-full text-xs border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500">
                <option disabled value="">Select Mould</option>
                <option v-for="mould in bom.moulds" :key="mould.mould_no" :value="mould.mould_no">
                  {{ mould.mould_no }} : {{ mould.mould_name }} ({{ mould.cavity_count }}C)
                </option>
              </select>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="!filteredBOMs.length && !loading"
      class="p-10 text-gray-400 text-center border-2 border-dashed border-gray-100 rounded-xl mt-4">
      No BOMs available for selected Sales Orders.
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed } from "vue";
import { api } from "../services/api";

const props = defineProps({
  salesOrders: { type: Array, default: () => [] },
  selected: { type: Array, default: () => [] },
});

const emit = defineEmits(["update:selected", "update:capBOMs", "bom-loaded"]);

const boms = ref([]);
const loading = ref(false);
const error = ref(null);
const selectedLocal = ref([]);
const search = ref("");

const headers = ["#", "Sales Order", "BOM", "FG Item", "Qty", "Type", "Customer", "Req Qty", "Cavity", "PCS wt", "Runner", "Shot", "Gross", "Cycle Time", "Machine (Workstation)", "Mould"];

const filteredBOMs = computed(() => {
  if (!search.value.trim()) return boms.value;
  const s = search.value.toLowerCase();
  return boms.value.filter(b => b.bom_no?.toLowerCase().includes(s) || b.item_code?.toLowerCase().includes(s));
});

const isAllSelected = computed(() => {
  return filteredBOMs.value.length > 0 && selectedLocal.value.length === filteredBOMs.value.length;
});


watch(() => boms.value, (newBoms) => {
  newBoms.forEach(bom => {
    const foundMould = bom.moulds.find(m => m.mould_no === bom.selected_mould);
    if (foundMould && bom.cavity !== foundMould.cavity_count) {
      bom.cavity = foundMould.cavity_count;
    }
  });
}, { deep: true });

watch([selectedLocal, boms], () => {
  const selectedData = boms.value.filter(b =>
    selectedLocal.value.some(s => s.row_uid === b.row_uid)
  );

  emit("update:selected", selectedData);
  emit("update:capBOMs", selectedData);
}, { deep: true });

const fetchBOMs = async () => {
  if (!props.salesOrders.length) {
    boms.value = [];
    selectedLocal.value = [];
    return;
  }

  loading.value = true;
  error.value = null;

  try {
    const res = await api.getBOMsForSalesOrder(props.salesOrders);
    boms.value = (res.data.message || []).map((b) => {
      const firstMould = b.moulds?.[0];
      return {
        ...b,
        row_uid: `${b.sales_order}::${b.item_code}::${b.bom_no}`,
        bom_operations: b.bom_operations || [],
        moulds: b.moulds || [],
        selected_workstation: b.bom_operations?.[0]?.workstation || "",
        selected_mould: firstMould?.mould_no || "",
        cavity: firstMould?.cavity_count || 0
      };
    });

    selectedLocal.value = [];
    emit("bom-loaded", boms.value);
  } catch (err) {
    error.value = "Failed to fetch BOMs.";
  } finally {
    loading.value = false;
  }
};

const selectAll = () => selectedLocal.value = [...filteredBOMs.value];
const unselectAll = () => selectedLocal.value = [];
const toggleSelectAll = () => isAllSelected.value ? unselectAll() : selectAll();

watch(() => props.salesOrders, fetchBOMs, { deep: true, immediate: true });
</script>