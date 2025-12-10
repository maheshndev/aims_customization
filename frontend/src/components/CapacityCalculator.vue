<template>
  <div class="p-5 bg-white rounded-xl shadow-sm">

    <!-- Title -->
    <h2 class="text-lg font-semibold mb-4">Capacity Planner</h2>

    <!-- Loading -->
    <div v-if="loading" class="text-gray-500 animate-pulse">Calculating...</div>

    <!-- Error -->
    <div v-if="error" class="bg-red-100 text-red-700 px-4 py-2 rounded mb-4">
      {{ error }}
    </div>

    <!-- Capacity Table -->
    <div v-if="capacity.length && !loading" class="overflow-x-auto">
      <table class="min-w-full border text-sm">
        <thead class="bg-gray-50">
          <tr>
            <th class="border p-2 text-left">BOM</th>
            <th class="border p-2 text-left">Item</th>
            <th class="border p-2 text-right">Cycle Time (sec)</th>
            <th class="border p-2 text-right">Cavity</th>
            <th class="border p-2 text-right">Required Qty</th>
            <th class="border p-2 text-right">Shots / hr</th>
            <th class="border p-2 text-right">Output / hr</th>
            <th class="border p-2 text-right">Machine Hrs Needed</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in capacity" :key="row.bom_no" class="hover:bg-gray-50">
            <td class="border p-2">{{ row.bom_no }}</td>
            <td class="border p-2">{{ row.item_code }}</td>
            <td class="border p-2 text-right">{{ row.cycle_time }}</td>
            <td class="border p-2 text-right">{{ row.cavity }}</td>
            <td class="border p-2 text-right">{{ row.required_qty }}</td>
            <td class="border p-2 text-right">{{ row.shots_per_hour }}</td>
            <td class="border p-2 text-right">{{ row.output_per_hour }}</td>
            <td
              class="border p-2 text-right font-semibold"
              :class="row.machine_hrs > row.available_machine_hrs ? 'text-red-600' : 'text-green-600'"
            >
              {{ row.machine_hrs.toFixed(2) }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Summary -->
    <div v-if="summary.total_machine_hrs" class="mt-6 p-4 bg-gray-100 rounded-xl">
      <h3 class="font-semibold text-lg mb-2">Summary</h3>
      <p>Total Required Machine Hours: <strong>{{ summary.total_machine_hrs.toFixed(2) }}</strong></p>
      <p>Available Machine Hours: <strong>{{ summary.available_machine_hrs }}</strong></p>
      <p
        class="mt-2"
        :class="summary.total_machine_hrs > summary.available_machine_hrs ? 'text-red-600' : 'text-green-600'"
      >
        {{
          summary.total_machine_hrs > summary.available_machine_hrs
            ? '⚠ Insufficient Capacity — Cannot release Work Order'
            : '✔ Capacity OK — Work Order can be released'
        }}
      </p>
    </div>

  </div>
</template>

<script setup>
import { ref, watch } from "vue";

const props = defineProps({
  boms: { type: Array, default: () => [] },
  availableMachineHours: { type: Number, default: 300 } // Default 300 hrs/month per machine
});

const emit = defineEmits(["capacity-updated"]);

const loading = ref(false);
const error = ref("");
const capacity = ref([]);
const summary = ref({ total_machine_hrs: 0, available_machine_hrs: 0 });

function calculateCapacity() {
  if (!props.boms?.length) return;

  loading.value = true;
  error.value = "";

  try {
    const cap = [];
    let totalHrs = 0;

    for (const bom of props.boms) {
      const cycleTime = parseFloat(bom.cycle_time || 0);
      const cavity = parseInt(bom.cavity || 1);
      const requiredQty = parseFloat(bom.required_for_selected_qty || 0);

      const shotsPerHour = cycleTime > 0 ? Math.floor(3600 / cycleTime) : 0;
      const outputPerHour = shotsPerHour * cavity;
      const hrsNeeded = outputPerHour > 0 ? requiredQty / outputPerHour : 9999;

      totalHrs += hrsNeeded;

      cap.push({
        bom_no: bom.bom_no,
        item_code: bom.item_code,
        cycle_time: cycleTime,
        cavity,
        required_qty: requiredQty,
        shots_per_hour: shotsPerHour,
        output_per_hour: outputPerHour,
        machine_hrs: hrsNeeded,
        available_machine_hrs: props.availableMachineHours
      });
    }

    capacity.value = cap;
    summary.value = {
      total_machine_hrs: totalHrs,
      available_machine_hrs: props.availableMachineHours
    };

    emit("capacity-updated", { capacity: cap, summary: summary.value });
  } catch (err) {
    error.value = err.message || "Capacity calculation failed";
  }

  loading.value = false;
}

watch(() => props.boms, calculateCapacity, { deep: true, immediate: true });
</script>
