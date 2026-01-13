<template>
  <div class="job-cards rounded shadow-sm p-4 bg-white">
    <div class="flex items-center gap-2 mb-3">
      <button @click="selectAll" :disabled="!jobCards.length" class="px-3 py-1 bg-blue-100 text-black rounded text-sm">
        Select All
      </button>
      <button @click="unselectAll" :disabled="!selectedJobCards.length"
        class="px-3 py-1 bg-gray-200 text-black rounded text-sm">
        Unselect All
      </button>
      <button class="px-3 py-1 bg-green-100 text-black rounded hover:bg-green-200" @click="refreshJobCards">
        🔄 Refresh
      </button>
      <span class="text-sm text-gray-500 ml-2">Selected: {{ selectedJobCards.length }}</span>
    </div>

    <div v-if="loading" class="text-gray-500">Loading Job Cards...</div>
    <div v-if="error" class="text-red-500 mb-2">{{ error }}</div>

    <div v-if="jobCards.length && !loading" class="overflow-auto rounded-b-2xl">
      <table class="table-auto min-w-[1400px] border-collapse w-full">
        <thead class="bg-gray-100 uppercase">
          <tr>
            <th class="border px-3 py-2 text-center">
              <input type="checkbox" :checked="isAllSelected" @change="toggleAll" />
            </th>
            <th class="border px-3 py-2">#</th>
            <th class="border px-3 py-2 whitespace-nowrap">Work Order</th>
            <th class="border px-3 py-2 whitespace-nowrap">Job Card</th>
            <th class="border px-3 py-2 whitespace-nowrap">Status</th>
            <th class="border px-3 py-2 whitespace-nowrap">Operation</th>
            <th class="border px-3 py-2 whitespace-nowrap">Workstation</th>
            <th class="border px-3 py-2 whitespace-nowrap">RM Item Code</th>
            <th class="border px-3 py-2 whitespace-nowrap">RM Item Name</th>
            <th class="border px-3 py-2 whitespace-nowrap">Required Qty</th>
            <th class="border px-3 py-2 whitespace-nowrap">Available Qty</th>
            <th class="border px-3 py-2 whitespace-nowrap">Consumed Qty</th>
            <th class="border px-3 py-2 whitespace-nowrap">Production Item</th>
            <th class="border px-3 py-2 whitespace-nowrap">Mould</th>
            <th class="border px-3 py-2 whitespace-nowrap">Expected Start</th>
            <th class="border px-3 py-2 whitespace-nowrap">Expected End</th>
            <th class="border px-3 py-2 whitespace-nowrap">Time (Mins)</th>
            <th class="border px-3 py-2 whitespace-nowrap">Completed Qty</th>
            <th class="border px-3 py-2 whitespace-nowrap">Process Loss</th>
            <th class="border px-3 py-2 whitespace-nowrap">Warehouse</th>
            <th class="border px-3 py-2 whitespace-nowrap">Quality Inspection</th>
            <th class="border px-3 py-2 whitespace-nowrap">Posting Date</th>
            <th class="border px-3 py-2 whitespace-nowrap">BOM No</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(jc, index) in jobCards" :key="jc.job_card" class="hover:bg-gray-50 transition">
            <td class="border px-3 py-2 text-center">
              <input type="checkbox" v-model="selectedIds" :value="jc.job_card" />
            </td>
            <td class="border px-3 py-2">{{ index + 1 }}</td>
            <td class="border px-3 py-2 whitespace-nowrap">{{ jc.work_order }}</td>
            <td class="border px-3 py-2 whitespace-nowrap">{{ jc.job_card }}</td>
            <td class="border px-3 py-2 whitespace-nowrap">
              {{ jc.job_card_status }}
            </td>
            <td class="border px-3 py-2 whitespace-nowrap">{{ jc.operation }}</td>
            <td class="border px-3 py-2 whitespace-nowrap">{{ jc.workstation }}</td>
            <td class="border px-3 py-2 whitespace-nowrap">{{ jc.rm_item_code }}</td>
            <td class="border px-3 py-2 whitespace-nowrap">{{ jc.rm_item_name }}</td>
            <td class="border px-3 py-2 whitespace-nowrap">{{ jc.required_qty }}</td>
            <td class="border px-3 py-2 whitespace-nowrap">{{ jc.available_qty }}</td>
            <td class="border px-3 py-2 whitespace-nowrap">{{ jc.consumed_qty }}</td>
            <td class="border px-3 py-2 whitespace-nowrap">
              {{ jc.production_item }}
            </td>
            <td class="border px-3 py-2 whitespace-nowrap">{{ jc.mould }}</td>
            <td class="border px-3 py-2 whitespace-nowrap">
              {{ jc.expected_start_date }}
            </td>
            <td class="border px-3 py-2 whitespace-nowrap">
              {{ jc.expected_end_date }}
            </td>
            <td class="border px-3 py-2 whitespace-nowrap">{{ jc.time_required }}</td>
            <td class="border px-3 py-2 whitespace-nowrap">
              {{ jc.total_completed_qty }}
            </td>
            <td class="border px-3 py-2 whitespace-nowrap">
              {{ jc.process_loss_qty }}
            </td>
            <td class="border px-3 py-2 whitespace-nowrap">{{ jc.wip_warehouse }}</td>
            <td class="border px-3 py-2 whitespace-nowrap">
              {{ jc.quality_inspection }}
            </td>
            <td class="border px-3 py-2 whitespace-nowrap">{{ jc.posting_date }}</td>
            <td class="border px-3 py-2 whitespace-nowrap">{{ jc.bom_no }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="!jobCards.length && !loading" class="text-gray-500 mt-2">
      No Job Cards found.
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed } from "vue";
import { api } from "../services/api";

const props = defineProps({
  workOrders: { type: Array, default: () => [] },
});

const emit = defineEmits(["update:selected"]);

const jobCards = ref([]);
const selectedIds = ref([]);
const loading = ref(false);
const error = ref(null);

const selectedJobCards = computed(() =>
  jobCards.value.filter((jc) => selectedIds.value.includes(jc.job_card))
);

const isAllSelected = computed(
  () => jobCards.value.length && selectedIds.value.length === jobCards.value.length
);

function selectAll() {
  selectedIds.value = jobCards.value.map((jc) => jc.job_card);
}
function unselectAll() {
  selectedIds.value = [];
}
function toggleAll(e) {
  e.target.checked ? selectAll() : unselectAll();
}

watch(selectedJobCards, (val) => {
  emit("update:selected", val);
});

async function fetchJobCards() {
  if (!props.workOrders.length) return;
  loading.value = true;
  error.value = null;
  selectedIds.value = [];

  try {
    const res = await api.getJobCards(props.workOrders);

    jobCards.value = res.data.message || [];
  } catch (err) {
    console.error("Job Card fetch failed:", err);
    error.value = "Failed to fetch Job Cards.";
    jobCards.value = [];
  } finally {
    loading.value = false;
  }
}
const refreshJobCards = async () => {
  jobCards.value = [];
  selectedIds.value = [];
  await fetchJobCards();
};
watch(() => props.workOrders, fetchJobCards, { immediate: true });
</script>
