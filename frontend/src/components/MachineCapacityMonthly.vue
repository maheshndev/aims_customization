<template>
  <div class="p-2 overflow-x-auto rounded-lg shadow-sm">
    <table class="w-full text-sm border border-gray-300">
      <thead class="bg-gray-100 text-gray-700">
        <tr>
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
        <tr
          v-for="r in rows"
          :key="r.machine"
          class="hover:bg-gray-50"
        >
          <td class="px-2 py-1 border">{{ r.machine }}</td>
          <td class="px-2 py-1 border">{{ r.month_days }}</td>
          <td class="px-2 py-1 border">{{ r.daily_capacity_hrs }}</td>
          <td class="px-2 py-1 border">{{ r.shifts }}</td>
          <td class="px-2 py-1 border">{{ r.utilization }}</td>
          <td class="px-2 py-1 border">{{ r.month_capacity }}</td>
          <td class="px-2 py-1 border">{{ r.required_hours }}</td>
          <td
            class="px-2 py-1 border font-semibold"
            :class="r.balance_hours < 0 ? 'text-red-600' : 'text-green-600'"
          >
            {{ r.balance_hours }}
          </td>
          <td class="px-2 py-1 border">{{ r.required_shifts }}</td>
        </tr>

        <tr v-if="!rows.length">
          <td colspan="9" class="text-center py-4 text-gray-500">
            No data available
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { ref, watch } from "vue";
import { api } from "../services/capavityApi";

/* ✅ Properly capture props */
const props = defineProps({
  filters: {
    type: Object,
    required: true
  }
});

const rows = ref([]);

/* ✅ Load data safely */
const loadData = async () => {
  const { customer, month, year } = props.filters;

  if (!customer || !month || !year) {
    rows.value = [];
    return;
  }

  try {
    const res = await api.getMachineCapacityMonthly(props.filters);

    // Frappe-style response safety
    rows.value = res?.data?.message || [];
  } catch (err) {
    console.error("Failed to load machine capacity", err);
    rows.value = [];
  }
};

/* ✅ React to filter changes */
watch(
  () => props.filters,
  loadData,
  { deep: true, immediate: true }
);
</script>
