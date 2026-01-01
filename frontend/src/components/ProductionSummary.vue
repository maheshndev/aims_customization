<template>
  <div class="space-y-4">
<!-- Refresh Button -->
      <button
        @click="refresh"
        :disabled="loading"
        class="ml-4 px-3 py-2 text-sm rounded border
               bg-white hover:bg-gray-50
               disabled:opacity-50 disabled:cursor-not-allowed"
      >
        🔄 Refresh
      </button>
    <!-- KPI Header + Refresh -->
    <div class="flex items-center justify-between">
      <div class="grid grid-cols-4 md:grid-cols-4 gap-2 flex-1">
        <Kpi label="Total Orders" :value="rows.length" />
        <Kpi label="Total Qty" :value="totalQty" />
        <Kpi label="Produced" :value="totalProduced" />
        <Kpi label="Completion %" :value="avgProgress + '%'" />
      </div>

      
    </div>

    <!-- Table -->
    <table class="min-w-[800px] table-auto divide-y divide-gray-200 border rounded-xl shadow-md">
      <thead class="bg-gray-100 uppercase">
        <tr>
          <th class="border px-3 py-2 whitespace-nowrap">#</th>
          <th class="border px-3 py-2 whitespace-nowrap">Item</th>
          <th class="border text-right px-3 py-2 whitespace-nowrap">Order</th>
          <th class="border text-right px-3 py-2 whitespace-nowrap">Produced</th>
          <th class="border text-right px-3 py-2 whitespace-nowrap">Balance</th>
          <th class="border px-3 py-2 whitespace-nowrap">Progress</th>
          <th class="border px-3 py-2 whitespace-nowrap">Status</th>
          <th class="border px-3 py-2 whitespace-nowrap">Timeline</th>
        </tr>
      </thead>

      <tbody>
        <tr v-for="(r,index) in rows" :key="r.item_code" class="border-b">
          <th class="border px-3 py-2 whitespace-nowrap">{{ index+1 }}</th>
          <td class="border font-medium px-3 py-2 whitespace-nowrap">{{ r.item_name }}</td>
          <td class="border text-right px-3 py-2 whitespace-nowrap">{{ r.order_qty }}</td>
          <td class="border text-right text-green-600 px-3 py-2 whitespace-nowrap">{{ r.produced_qty }}</td>
          <td class="border text-right text-red-500 px-3 py-2 whitespace-nowrap">{{ r.balance_qty }}</td>

          <td class="border min-w-[160px] px-3 py-2 whitespace-nowrap">
            <ProductionProgress
              :total="r.order_qty"
              :produced="r.produced_qty"
              :progress="r.progress"
            />
          </td>

          <td class="border px-3 py-2 whitespace-nowrap">
            <StatusBadge :status="r.status" />
          </td>

          <td class="border min-w-[240px] px-3 py-2 whitespace-nowrap">
            <GanttMini :bars="r.timeline" />
          </td>
        </tr>
      </tbody>
    </table>
    <!-- Charts -->
    <ProductionCharts :rows="rows" />
  </div>
</template>
<script setup>
import { computed, ref, watch } from "vue"
import { api } from "../services/api"

import StatusBadge from "./StatusBadge.vue"
import GanttMini from "./GanttMini.vue"
import ProductionProgress from "./ProductionProgress.vue"
import ProductionCharts from "./ProductionCharts.vue"
import Kpi from "./Kpi.vue"

const props = defineProps({
  filters: { type: Object, required: true },
})

const rows = ref([])
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    const res = await api.getProductionControlDashboard(props.filters)
    rows.value = res?.data?.message.data || []
    console.log(res.data.message.data);
    
  } finally {
    loading.value = false
  }
}

function refresh() {
  load()
}

watch(
  () => props.filters,
  () => {
    load()
  },
  { deep: true, immediate: true }
)

const totalQty = computed(() =>
  rows.value.reduce((a, r) => a + r.order_qty, 0)
)

const totalProduced = computed(() =>
  rows.value.reduce((a, r) => a + r.produced_qty, 0)
)

const avgProgress = computed(() =>
  rows.value.length
    ? Math.round(
        rows.value.reduce((a, r) => a + r.progress, 0) / rows.value.length
      )
    : 0
)
</script>
