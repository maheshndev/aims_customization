<template>
  <div class="p-2 overflow-x-auto rounded-lg shadow-sm bg-white">
    <div v-if="loading" class="text-gray-500 animate-pulse">Loading ...</div>

    <div v-if="error" v-html="error" class="bg-red-100 text-red-700 px-4 py-2 border rounded mb-4" />

    <div v-if="rows.length && !loading" class="flex justify-start gap-3 mb-3">
      <button class="px-3 py-1 bg-blue-100 text-black rounded" @click="selectAll">
        Select All
      </button>
      <button class="px-3 py-1 bg-gray-200 text-black rounded" @click="unselectAll">
        Unselect All
      </button>
      <button class="px-3 py-1 bg-green-100 text-black rounded hover:bg-green-200" @click="refreshAll">
        🔄 Refresh
      </button>
    </div>

    <table class="w-full text-sm border border-gray-300">
      <thead class="bg-gray-100 text-gray-700">
        <tr>
          <th class="px-2 py-1 border w-10 text-center">
            <input type="checkbox" :checked="isSelectedAll" @change="toggleSelectAll" />
          </th>
          <th class="px-2 py-1 border">#</th>
          <th class="px-2 py-1 border">Machine</th>
          <th class="px-2 py-1 border">Month Days</th>
          <th class="px-2 py-1 border">Daily Hrs</th>
          <th class="px-2 py-1 border">Shifts</th>
          <th class="px-2 py-1 border">Utilization %</th>
          <th class="px-2 py-1 border">Capacity Hrs</th>
          <th class="px-2 py-1 border">Required Hrs</th>
          <th class="px-2 py-1 border">Balance</th>
          <th class="px-2 py-1 border">Req Shifts</th>
          <th class="px-2 py-1 border"></th>
        </tr>
      </thead>

      <tbody>
        <tr v-for="(row, index) in rows" :key="row.machine" class="hover:bg-gray-50">
          <td class="px-2 py-1 border text-center">
            <input type="checkbox" :value="row.machine" v-model="selectedLocal" />
          </td>
          <td class="px-2 py-1 border">{{ index + 1 }}</td>
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
          <td colspan="11" class="text-center py-4 text-gray-500">No data available</td>
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
});

const emit = defineEmits(["update:selected"]);

const loading = ref(false);
const error = ref(null);
const rows = ref([]);
const selectedLocal = ref([]);

const isSelectedAll = computed(
  () => rows.value.length > 0 && selectedLocal.value.length === rows.value.length
);

const selectAll = () => {
  selectedLocal.value = rows.value.map((r) => r.machine);
  emit("update:selected", [...selectedLocal.value]);
};

const unselectAll = () => {
  selectedLocal.value = [];
  emit("update:selected", []);
};

const toggleSelectAll = () => (isSelectedAll.value ? unselectAll() : selectAll());

watch(selectedLocal, () => {
  emit("update:selected", [...selectedLocal.value]);
});

const loadMachineCapacity = async () => {
  loading.value = true;
  error.value = null;
  rows.value = [];
  selectedLocal.value = [];

  try {
    const res = await api.getMachineCapacityMonthly(props.filters);
    const payload = res?.data?.message;

    if (!payload?.success) {
      throw new Error(payload?.message || "Invalid server response");
    }

    rows.value = payload.data || [];

    // success but empty
    if (!rows.value.length) {
      frappe.msgprint({
        title: "No Data",
        message: payload.message,
        indicator: "orange",
      });
    }
  } catch (err) {
    const msg = extractFrappeError(err);
    error.value = msg;

    frappe.msgprint({
      title: "Load Failed",
      message: msg,
      indicator: "red",
    });
  } finally {
    loading.value = false;
  }
};

const refreshAll = async () => {
  await loadMachineCapacity();
};

watch(
  () => props.filters,
  () => {
    loadMachineCapacity();
  },
  { immediate: true, deep: true }
);
</script>
