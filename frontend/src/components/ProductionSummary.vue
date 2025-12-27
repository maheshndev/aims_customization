<template>
  <div class="bg-white rounded-xl shadow p-4 space-y-6">
    <!-- KPI LIST -->
    <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
      <div v-for="k in kpis" :key="k.label" class="bg-gray-50 p-3 rounded text-center">
        <div class="text-xs text-gray-500">{{ k.label }}</div>
        <div class="text-lg font-semibold">{{ k.value }}</div>
      </div>
    </div>

    <!-- CHART -->
    <canvas v-if="items.length" ref="chartRef" class="w-full" style="min-height: 350px"></canvas>

    <!-- ITEMS TABLE -->
    <div v-if="items.length" class="overflow-auto">
      <h3 class="text-sm font-semibold mb-2 text-gray-700">Production Items Summary</h3>
      <table class="min-w-[1200px] border-collapse w-full text-sm">
        <thead class="bg-gray-100">
          <tr>
            <th class="th">#</th>
            <th class="th">Item</th>
            <th class="th">Order Qty</th>
            <th class="th">Planned</th>
            <th class="th">Produced</th>
            <th class="th">Pending</th>
            <th class="th">WIP</th>
            <th class="th">Stock</th>
            <th class="th">Dispatched</th>
            <th class="th">Balance</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(r, i) in items" :key="r.item_code || i">
            <td class="td">{{ i + 1 }}</td>
            <td class="td font-medium">{{ r.item_name }}</td>
            <td class="td">{{ r.order_qty }}</td>
            <td class="td">{{ r.planned_qty }}</td>
            <td class="td text-green-600 font-semibold">{{ r.produced_qty }}</td>
            <td class="td text-orange-600">{{ r.pending_qty }}</td>
            <td class="td text-purple-600">{{ r.wip_qty }}</td>
            <td class="td">{{ r.available_stock }}</td>
            <td class="td text-blue-600">{{ r.dispatched_qty }}</td>
            <td class="td text-red-600">{{ r.balance_to_dispatch }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- WORK ORDER TRACKING TABLE -->
    <div v-if="trackingDetails.length" class="overflow-auto">
      <h3 class="text-sm font-semibold mb-2 text-gray-700">Work Order Tracking</h3>
      <table class="min-w-[1400px] border-collapse w-full text-xs">
        <thead class="bg-blue-50">
          <tr>
            <th class="th">WO #</th>
            <th class="th">Sales Order</th>
            <th class="th">Item</th>
            <th class="th">Ordered</th>
            <th class="th">Produced</th>
            <th class="th">Progress</th>
            <th class="th">Status</th>
            <th class="th">Job Cards</th>
            <th class="th">Start Date</th>
            <th class="th">End Date</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="t in trackingDetails" :key="t.wo_name" class="hover:bg-gray-50">
            <td class="td font-mono text-blue-600">{{ t.wo_name }}</td>
            <td class="td">{{ t.sales_order }}</td>
            <td class="td">{{ t.production_item }}</td>
            <td class="td">{{ t.ordered_qty }}</td>
            <td class="td text-green-600 font-semibold">{{ t.produced_qty }}</td>
            <td class="td">
              <div class="flex items-center gap-2">
                <div class="w-16 h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div class="h-full bg-blue-500" :style="{ width: t.progress_percentage + '%' }"></div>
                </div>
                <span>{{ t.progress_percentage }}%</span>
              </div>
            </td>
            <td class="td">
              <span :class="{
                'bg-green-100 text-green-800': t.status_state === 'Completed',
                'bg-blue-100 text-blue-800': t.status_state === 'In Progress',
                'bg-gray-100 text-gray-800': t.status_state === 'Pending'
              }" class="px-2 py-1 rounded text-xs font-semibold">
                {{ t.status_state }}
              </span>
            </td>
            <td class="td text-center">
              <span class="text-xs">{{ t.job_cards_completed }}/{{ t.job_cards_submitted + t.job_cards_in_progress + t.job_cards_completed }}</span>
            </td>
            <td class="td">{{ formatDate(t.planned_start) }}</td>
            <td class="td">{{ formatDate(t.planned_end) }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- WORKSTATION SUMMARY TABLE -->
    <div v-if="workstationSummary.length" class="overflow-auto">
      <h3 class="text-sm font-semibold mb-2 text-gray-700">Workstation Utilization</h3>
      <table class="min-w-[1000px] border-collapse w-full text-sm">
        <thead class="bg-amber-50">
          <tr>
            <th class="th">Workstation</th>
            <th class="th">Type</th>
            <th class="th">Items Assigned</th>
            <th class="th">Items Produced</th>
            <th class="th">Pending</th>
            <th class="th">Utilization</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="ws in workstationSummary" :key="ws.workstation">
            <td class="td font-medium">{{ ws.workstation }}</td>
            <td class="td">{{ ws.type }}</td>
            <td class="td">{{ ws.total_items_assigned }}</td>
            <td class="td text-green-600 font-semibold">{{ ws.total_items_produced }}</td>
            <td class="td text-orange-600">{{ ws.pending }}</td>
            <td class="td">
              <div class="flex items-center gap-2">
                <div class="w-20 h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div class="h-full bg-amber-500" :style="{ width: getUtilization(ws) + '%' }"></div>
                </div>
                <span class="text-xs">{{ getUtilization(ws) }}%</span>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="!loading && errorMsg" class="text-red-500 text-center">
      {{ errorMsg }}
    </div>
    <div v-else-if="!items.length && !loading" class="text-gray-500 text-center">
      No production data found
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick, onBeforeUnmount } from "vue"
import { Chart, registerables } from "chart.js"
import { api } from "../services/api"

Chart.register(...registerables)

const props = defineProps({
  filters: { type: Object, required: true },
})

const items = ref([])
const totals = ref({})
const trackingDetails = ref([])
const workstationSummary = ref([])
const loading = ref(false)
const chart = ref(null)
const chartRef = ref(null)

const kpis = ref([])
let abortController = null
const errorMsg = ref("")

/* ---------------- HELPER FUNCTIONS ---------------- */
function formatDate(dateStr) {
  if (!dateStr) return "-"
  try {
    const date = new Date(dateStr)
    return date.toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" })
  } catch {
    return dateStr
  }
}

function getUtilization(ws) {
  if (!ws || ws.total_items_assigned === 0) return 0
  return Math.round((ws.total_items_produced / ws.total_items_assigned) * 100)
}

/* ---------------- SAFE LOAD ---------------- */
async function load() {
  const { customer, month, year } = props.filters || {}

  errorMsg.value = ""
  if (!customer) {
    items.value = []
    totals.value = {}
    errorMsg.value = "Please select customer."
    destroyChart()
    return
  }

  // 🔴 cancel previous request
  
  abortController?.abort()
  abortController = new AbortController()
  
  loading.value = true
  
  try {
    const res = await api.getProductionSummary(
      customer,
      month,
      year,
      { signal: abortController.signal }
    )

    const data = res?.data?.message
    if (data && Array.isArray(data.items) && data.items.length) {
      items.value = data.items
      totals.value = data.totals || {}
      errorMsg.value = ""
    } else {
      items.value = []
      totals.value = {}
      errorMsg.value = "No production data found."
    }

    kpis.value = [
      { label: "Planned", value: totals.value.planned || 0 },
      { label: "Produced", value: totals.value.produced || 0 },
      { label: "Pending", value: totals.value.pending || 0 },
      { label: "WIP", value: totals.value.wip || 0 },
      { label: "Dispatched", value: totals.value.dispatched || 0 }
    ]

    await nextTick()
    renderChart()

  } catch (err) {
    if (err.name !== "CanceledError") {
      errorMsg.value = err?.response?.data?.message || err.message || "Unknown error"
      destroyChart()
      items.value = []
      totals.value = {}
    }
  } finally {
    loading.value = false
  }
}

/* ---------------- CHART HANDLING ---------------- */
function renderChart() {
  if (!chartRef.value || !items.value.length) return

  destroyChart()
  try {
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
        plugins: {
          legend: { position: "top" }
        },
        scales: {
          y: { beginAtZero: true }
        }
      }
    })
  } catch (e) {
    // Chart.js error, destroy chart and show error
    destroyChart()
    errorMsg.value = "Chart rendering error"
  }
}

function destroyChart() {
  if (chart.value) {
    chart.value.destroy()
    chart.value = null
  }
}

/* ---------------- WATCH FILTERS ---------------- */
watch(
  () => props.filters,
  () => load(),
  { deep: true, immediate: true }
)

/* ---------------- CLEANUP ---------------- */
onBeforeUnmount(() => destroyChart())
</script>
