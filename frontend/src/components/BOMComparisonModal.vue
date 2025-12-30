<template>
  <div v-if="open" class="fixed inset-0 bg-black bg-opacity-40 flex items-center justify-center z-50">
    <div class="bg-white rounded-xl shadow-xl w-11/12 max-w-6xl p-6 relative">

      <div class="flex justify-between items-center mb-4">
        <h2 class="text-xl font-semibold">BOM Comparison</h2>
        <button @click="closeModal" class="text-gray-500 hover:text-black text-xl">✕</button>
      </div>

      <div v-if="boms.length < 2" class="text-red-600 font-medium text-center py-4">
        Please select at least 2 BOMs to compare.
      </div>

      <div v-if="boms.length >= 2" class="overflow-x-auto">

        <table class="min-w-full border border-gray-300 rounded-md">
          <thead>
            <tr class="bg-gray-100">
              <th class="border px-3 py-2 text-left w-40">Field</th>
              <th v-for="bom in boms"
                  :key="bom.bom_no"
                  class="border px-3 py-2 text-left">
                {{ bom.bom_no }}
              </th>
            </tr>
          </thead>

          <tbody>
            <template v-for="field in fields">
              <tr>
                <td class="border px-3 py-2 font-medium bg-gray-50">{{ field.label }}</td>

                <td v-for="bom in boms"
                    :key="field.key + bom.bom_no"
                    :class="[
                      'border px-3 py-2',
                      isDifferent(field.key) ? 'bg-red-100' : ''
                    ]">
                  {{ bom[field.key] }}
                </td>
              </tr>
            </template>
          </tbody>
        </table>

      </div>

      <div class="mt-6">
        <h3 class="text-lg font-semibold mb-2">Raw Material Comparison</h3>

        <table class="min-w-full border border-gray-300 rounded-md">
          <thead>
            <tr class="bg-gray-100">
              <th class="border px-3 py-2 text-left">RM Item</th>

              <th v-for="bom in boms" :key="'rm-header-' + bom.bom_no"
                class="border px-3 py-2 text-left">
                {{ bom.bom_no }}
              </th>
            </tr>
          </thead>

          <tbody>
            <tr v-for="rm in allRawMaterials" :key="rm">
              <td class="border px-3 py-2 bg-gray-50 font-medium">{{ rm }}</td>

              <td v-for="bom in boms"
                  :key="'rm-' + rm + '-' + bom.bom_no"
                  :class="[
                    'border px-3 py-2',
                    isRawMaterialDifferent(rm) ? 'bg-red-100' : ''
                  ]">
                {{
                  (rawMaterials[bom.bom_no]?.find(r => r.rm_item_code === rm)?.total_required_qty) || 0
                }}
              </td>
            </tr>
          </tbody>
        </table>

      </div>

      <div class="mt-6 text-right">
        <button
          @click="closeModal"
          class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Close
        </button>
      </div>

    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  open: Boolean,
  boms: { type: Array, default: () => [] },          
  rawMaterials: { type: Object, default: () => ({}) } 
});

const emit = defineEmits(["close"]);

const fields = [
  { key: "item_code", label: "Item Code" },
  { key: "bom_qty", label: "BOM Qty" },
  { key: "required_for_selected_qty", label: "Required Qty" },
  { key: "cavity", label: "Cavity" },
  { key: "pcs_wt", label: "PCS Weight" },
  { key: "runner_wt", label: "Runner Weight" },
  { key: "shot_wt", label: "Shot Weight" },
  { key: "gross_wt", label: "Gross Weight" },
  { key: "cycle_time", label: "Cycle Time" },
  { key: "uom", label: "UOM" },
];

const isDifferent = (key) => {
  const values = props.boms.map(b => b[key]);
  return new Set(values).size > 1;
};

const allRawMaterials = computed(() => {
  const set = new Set();
  for (const bomNo in props.rawMaterials) {
    props.rawMaterials[bomNo].forEach(rm => set.add(rm.rm_item_code));
  }
  return [...set];
});

const isRawMaterialDifferent = (rmCode) => {
  const values = props.boms.map(b => {
    const rm = props.rawMaterials[b.bom_no]?.find(r => r.rm_item_code === rmCode);
    return rm?.total_required_qty || 0;
  });

  return new Set(values).size > 1;
};

const closeModal = () => emit("close");

</script>
