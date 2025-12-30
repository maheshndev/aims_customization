<template>
  <div class="p-2 overflow-x-auto rounded-lg shadow-sm">
    <table class="w-full text-xs border border-gray-300">
      <thead class="bg-gray-100 text-gray-700">
        <tr>
          <th class="border px-2 py-1">Customer</th>
          <th class="border px-2 py-1">SO</th>
          <th class="border px-2 py-1">Item</th>
          <th class="border px-2 py-1">Qty</th>
          <th class="border px-2 py-1">Machine</th>
          <th class="border px-2 py-1">Pcs/Hr</th>
          <th class="border px-2 py-1">Loading Hrs</th>
        </tr>
      </thead>

      <tbody>
        <tr
          v-for="r in rows"
          :key="`${r.sales_order}-${r.item_code}`"
          class="hover:bg-gray-50"
        >
          <td class="border px-2 py-1">{{ r.customer }}</td>
          <td class="border px-2 py-1">{{ r.sales_order }}</td>
          <td class="border px-2 py-1">{{ r.item_name }}</td>
          <td class="border px-2 py-1">{{ r.schedule_qty }}</td>
          <td class="border px-2 py-1">{{ r.machine }}</td>
          <td class="border px-2 py-1">{{ r.machine_hourly_capacity }}</td>
          <td class="border px-2 py-1">{{ r.loading_hours }}</td>
        </tr>

        <tr v-if="!rows.length">
          <td colspan="7" class="text-center py-4 text-gray-500">
            No item loading data available
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { ref, watch } from "vue";
import { api } from "../services/capavityApi";

/* ✅ Capture props properly */
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
    const res = await api.getItemCapacityMonthly(props.filters);

    // Frappe-safe response handling
    rows.value = res?.data?.message || [];
  } catch (err) {
    console.error("Failed to load item capacity data", err);
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
