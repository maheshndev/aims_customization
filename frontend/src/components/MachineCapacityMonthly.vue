<template>
  <div class="p-2 overflow-x-auto rounded-lg shadow-sm bg-white">
    <table class="w-full text-sm border border-gray-300">
      <thead class="bg-gray-100 text-gray-700">
        <tr>
          <th class="px-2 py-1 border w-10 text-center">
            <input type="checkbox" :checked="allSelected" @change="toggleAll" />
          </th>
          <th class="px-2 py-1 border">Machine</th>
          <th class="px-2 py-1 border">Month Days</th>
          <th class="px-2 py-1 border">Daily Hrs</th>
          <th class="px-2 py-1 border">Shifts</th>
          <th class="px-2 py-1 border">Util %</th>
          <th class="px-2 py-1 border">Capacity Hrs</th>
          <th class="px-2 py-1 border">Required Hrs</th>
          <th class="px-2 py-1 border">Balance</th>
          <th class="px-2 py-1 border">Req Shifts</th>
        </tr>
      </thead>

      <tbody>
        <tr v-for="row in rows" :key="row.machine" class="hover:bg-gray-50">
          <td class="px-2 py-1 border text-center">
            <input type="checkbox" :value="row.machine" v-model="localSelected" />
          </td>

          <td class="px-2 py-1 border">{{ row.machine }}</td>
          <td class="px-2 py-1 border">{{ row.month_days }}</td>
          <td class="px-2 py-1 border">{{ row.daily_capacity_hrs }}</td>
          <td class="px-2 py-1 border">{{ row.shifts }}</td>
          <td class="px-2 py-1 border">{{ row.utilization }}</td>
          <td class="px-2 py-1 border">{{ row.month_capacity }}</td>
          <td class="px-2 py-1 border">{{ row.required_hours }}</td>
          <td class="px-2 py-1 border font-semibold" :class="row.balance_hours < 0 ? 'text-red-600' : 'text-green-600'">
            {{ row.balance_hours }}
          </td>
          <td class="px-2 py-1 border">{{ row.required_shifts }}</td>
        </tr>

        <tr v-if="!rows.length">
          <td colspan="10" class="text-center py-4 text-gray-500">No data available</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { ref, watch, computed } from "vue";
import { api } from "../services/capavityApi";

const props = defineProps({
  filters: { type: Object, required: true },
  selectedMachines: { type: Array, required: true },
});

const emit = defineEmits(["update:selectedMachines"]);

const rows = ref([]);
const localSelected = ref([]);

watch(
  () => props.selectedMachines,
  (val) => {
    localSelected.value = [...val];
  },
  { immediate: true }
);

watch(localSelected, (val) => {
  emit("update:selectedMachines", val); // ✅ FIXED
});

const allSelected = computed(() => {
  return rows.value.length > 0 &&
    localSelected.value.length === rows.value.length;
});

const toggleAll = (e) => {
  localSelected.value = e.target.checked
    ? rows.value.map(r => r.machine)
    : [];
};

const loadMachineCapacity = async () => {
  const { month, year } = props.filters || {};

  if (!month || !year) {
    rows.value = [];
    return;
  }

  try {
    const res = await api.getMachineCapacityMonthly(props.filters);
    rows.value = res?.data?.message || [];
   
  } catch (e) {
    console.error("Machine capacity failed", e);
    rows.value = [];
  }
};

watch(
  () => [props.filters.month, props.filters.year],
  loadMachineCapacity,
  { immediate: true }
);
</script>
