<template>
  <div class="bg-white rounded-xl shadow p-4 space-y-6">

    <!-- KPI SUMMARY -->
    <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
      <div
        v-for="k in kpis"
        :key="k.label"
        class="bg-gray-50 p-3 rounded text-center"
      >
        <div class="text-xs text-gray-500">{{ k.label }}</div>
        <div class="text-lg font-semibold">{{ k.value }}</div>
      </div>
    </div>

    <!-- BAR CHART -->
    <canvas
      v-if="items.length"
      ref="chartRef"
      class="w-full"
      style="min-height: 350px"
    />

    <!-- ITEMS TABLE -->
    <div v-if="items.length" class="overflow-auto">
      <h3 class="text-sm font-semibold mb-2 text-gray-700">
        Production Items Summary
      </h3>

      <table class="min-w-[1200px] w-full border-collapse text-sm">
        <thead class="bg-gray-100">
          <tr>
            <th class="th whitespace-nowrap">#</th>
            <th class="th whitespace-nowrap">Item</th>
            <th class="th whitespace-nowrap">Order Qty</th>
            <th class="th whitespace-nowrap">Planned</th>
            <th class="th whitespace-nowrap">Produced</th>
            <th class="th whitespace-nowrap">Pending</th>
            <th class="th whitespace-nowrap">WIP</th>
            <th class="th whitespace-nowrap">Stock</th>
            <th class="th whitespace-nowrap">Dispatched</th>
            <th class="th whitespace-nowrap">Balance</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(r, i) in items" :key="r.item_code || i">
            <td class="td">{{ i + 1 }}</td>
            <td class="td whitespace-nowrap font-medium">{{ r.item_name }}</td>
            <td class="td whitespace-nowrap">{{ r.order_qty }}</td>
            <td class="td whitespace-nowrap">{{ r.planned_qty }}</td>
            <td class="td whitespace-nowrap text-green-600 font-semibold">{{ r.produced_qty }}</td>
            <td class="td whitespace-nowrap text-orange-600">{{ r.pending_qty }}</td>
            <td class="td whitespace-nowrap text-purple-600">{{ r.wip_qty }}</td>
            <td class="td whitespace-nowrap">{{ r.available_stock }}</td>
            <td class="td whitespace-nowrap text-blue-600">{{ r.dispatched_qty }}</td>
            <td class="td whitespace-nowrap text-red-600">{{ r.balance_to_dispatch }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- EMPTY / ERROR STATES -->
    <div v-if="!loading && errorMsg" class="text-red-500 text-center">
      {{ errorMsg }}
    </div>

    <div v-else-if="!loading && !items.length" class="text-gray-500 text-center">
      No production data found
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed, nextTick, onBeforeUnmount } from "vue"
import { Chart, registerables } from "chart.js"
import { api } from "../services/api"

Chart.register(...registerables)

/* -------------------------------- PROPS -------------------------------- */
const props = defineProps({
  filters: { type: Object, required: true }
})

/* -------------------------------- STATE -------------------------------- */
const items = ref([])
const totals = ref({})
const loading = ref(false)
const errorMsg = ref("")

const chart = ref(null)
const chartRef = ref(null)

let abortController = null

/* -------------------------------- COMPUTED ----------------------------- */
const kpis = computed(() => [
  { label: "Planned", value: totals.value.planned || 0 },
  { label: "Produced", value: totals.value.produced || 0 },
  { label: "Pending", value: totals.value.pending || 0 },
  { label: "WIP", value: totals.value.wip || 0 },
  { label: "Dispatched", value: totals.value.dispatched || 0 }
])

/* -------------------------------- HELPERS ------------------------------ */
function resetState(message = "") {
  items.value = []
  totals.value = {}
  errorMsg.value = message
  destroyChart()
}

function destroyChart() {
  if (chart.value) {
    chart.value.destroy()
    chart.value = null
  }
}

/* -------------------------------- CHART -------------------------------- */
function renderChart() {
  if (!chartRef.value || !items.value.length) return

  destroyChart()

  chart.value = new Chart(chartRef.value, {
    type: "bar",
    data: {
      labels: items.value.map(i => i.item_name),
      datasets: [
        { label: "Planned", data: items.value.map(i => i.planned_qty) },
        { label: "Produced", data: items.value.map(i => i.produced_qty) },
        { label: "Pending", data: items.value.map(i => i.pending_qty) }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: { beginAtZero: true }
      },
      plugins: {
        legend: { position: "top" }
      }
    }
  })
}

/* -------------------------------- LOAD --------------------------------- */
async function load() {
  const { customer, month, year } = props.filters || {}

  if (!customer) {
    resetState("Please select customer.")
    return
  }

  abortController?.abort()
  abortController = new AbortController()

  loading.value = true
  errorMsg.value = ""

  try {
    const res = await api.getProductionSummary(
      customer,
      month,
      year,
      { signal: abortController.signal }
    )

    const data = res?.data?.message

    if (!data?.items?.length) {
      resetState("No production data found.")
      return
    }

    items.value = data.items
    totals.value = data.totals || {}

    await nextTick()
    renderChart()

  } catch (err) {
    if (err.name !== "CanceledError") {
      resetState(
        err?.response?.data?.message ||
        err.message ||
        "Failed to load production data"
      )
    }
  } finally {
    loading.value = false
  }
}

/* -------------------------------- WATCH -------------------------------- */
watch(
  () => props.filters,
  load,
  { deep: true, immediate: true }
)

/* -------------------------------- CLEANUP ------------------------------ */
onBeforeUnmount(() => {
  abortController?.abort()
  destroyChart()
})
</script>
