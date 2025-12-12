<template>
  <div class="job-cards rounded shadow-sm p-4 bg-white">

    <!-- Loading -->
    <div v-if="loading" class="text-gray-500">Loading Job Cards...</div>

    <!-- Error -->
    <div v-if="error" class="text-red-500 mb-2">{{ error }}</div>

    <!-- Table -->
    <div v-if="jobCards.length && !loading" class="overflow-auto rounded-b-2xl">
      <table class="table-auto min-w-[1200px] border-collapse w-full">
        <thead class="bg-gray-100">
          <tr>
            <th class="border px-3 py-2 text-left">Job Card</th>
            <th class="border px-3 py-2 text-left">Status</th>
            <th class="border px-3 py-2 text-left">Operation</th>
            <th class="border px-3 py-2 text-left">Workstation</th>
            <th class="border px-3 py-2 text-left">RM Item Code</th>
            <th class="border px-3 py-2 text-left">RM Item Name</th>
            <th class="border px-3 py-2 text-left">Required Qty</th>
            <th class="border px-3 py-2 text-left">Available Qty</th>
            <th class="border px-3 py-2 text-left">Consumed Qty</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="jc in jobCards" :key="jc.name" class="hover:bg-gray-50 transition">
            <td class="border px-3 py-2">{{ jc.job_card }}</td>
            <td class="border px-3 py-2">{{ jc.job_card_status }}</td>
            <td class="border px-3 py-2">{{ jc.operation }}</td>
            <td class="border px-3 py-2">{{ jc.workstation }}</td>
            <td class="border px-3 py-2">{{ jc.rm_item_code }}</td>
            <td class="border px-3 py-2">{{ jc.rm_item_name }}</td>
            <td class="border px-3 py-2">{{ jc.required_qty }}</td>
            <td class="border px-3 py-2">{{ jc.available_qty }}</td>
            <td class="border px-3 py-2">{{ jc.consumed_qty }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- No Data -->
    <div v-if="!jobCards.length && !loading" class="text-gray-500 mt-2">
      No Job Cards found.
    </div>

  </div>
</template>

<script setup>
import { ref, watch } from "vue";
import { api } from "../services/api";

const props = defineProps({
  workOrders: { type: Array, default: () => [] }
});

const emit = defineEmits(["update:selected", "jc-loaded"]);

const jobCards = ref([]);
const loading = ref(false);
const error = ref(null);

const fetchJobCards = async () => {
  if (!props.workOrders?.length) {
    jobCards.value = [];
    emit("update:selected", []);
    emit("jc-loaded", []);
    return;
  }

  loading.value = true;
  error.value = null;

  try {
    const res = await api.getJobCards(props.workOrders);
	console.log("in job cards: ", res);
	console.log("in job card work order list :", props);
	
	
    const validCards = res?.data?.message?.filter(jc => jc?.name) || [];
    jobCards.value = validCards;

    emit("update:selected", validCards);
    emit("jc-loaded", validCards);

  } catch (err) {
    console.error(err);
    error.value = "Failed to fetch Job Cards.";
    jobCards.value = [];
    emit("update:selected", []);
    emit("jc-loaded", []);
  } finally {
    loading.value = false;
  }
};

// Watch for changes in work orders and fetch job cards
watch(
  () => props.workOrders,
  (newVal) => {
    if (!newVal || !newVal.length || newVal.includes(undefined)) {
      jobCards.value = [];
      emit("update:selected", []);
      emit("jc-loaded", []);
      return;
    }
    fetchJobCards();
  },
  { deep: true, immediate: true }
);
</script>
