<template>
  <div class="grid grid-cols-1 md:grid-cols-2 gap-2">

    <!-- Progress Distribution -->
    <div class="p-4 rounded shadow-md h-[600px] min-h-[450px] m-2">
      <h4 class="text-sm font-semibold mb-2">Production Progress (%)</h4>
      <Bar :data="progressData" :options="barOptions" />
    </div>

    <!-- Quantity + Trend -->
    <div class="grid grid-cols-2 md:grid-cols-2 gap-1">

      <div class="p-4 rounded shadow-md h-[600px] ">
        <h4 class="text-sm font-semibold mb-2">Qty Overview</h4>
        <Doughnut :data="qtyData" />
      </div>

      <div class="p-4 rounded shadow-md h-[600px]">
        <h4 class="text-sm font-semibold mb-2">Production Trend</h4>
        <!-- FIXED LINE CHART -->
        <Line :data="lineData" :options="lineOptions" />
      </div>

    </div>
  </div>
</template>

<script setup>
import { computed } from "vue"
import { Line, Bar, Doughnut } from "vue-chartjs"
import {
  Chart as ChartJS,
  BarElement,
  CategoryScale,
  LinearScale,
  ArcElement,
  Tooltip,
  Legend,
  LineElement,
  PointElement,
  Filler,
} from "chart.js"

ChartJS.register(
  BarElement,
  CategoryScale,
  LinearScale,
  ArcElement,
  Tooltip,
  Legend,
  LineElement,
  PointElement,
  Filler
)

const props = defineProps({
  rows: {
    type: Array,
    default: () => []
  }
})

/* ---------------- BAR ---------------- */
const progressData = computed(() => ({
  labels: props.rows.map(r => r.item_code),
  datasets: [
    {
      label: "Progress %",
      data: props.rows.map(r => r.progress),
      backgroundColor: "#3b82f6"
    }
  ]
}))

const barOptions = {
  responsive: true,
  maintainAspectRatio: false,
  scales: {
    y: {
      max: 100,
      ticks: { callback: v => v + "%" }
    }
  }
}

/* ---------------- DOUGHNUT ---------------- */
const qtyData = computed(() => {
  const total = props.rows.reduce((a, r) => a + r.order_qty, 0)
  const produced = props.rows.reduce((a, r) => a + r.produced_qty, 0)

  return {
    labels: ["Produced", "Balance"],
    datasets: [
      {
        data: [produced, Math.max(total - produced, 0)],
        backgroundColor: ["#10b981", "#e5e7eb"]
      }
    ]
  }
})

/* ---------------- LINE (FIXED) ---------------- */
const lineData = computed(() => ({
  labels: props.rows.map(r => r.item_code),
  datasets: [
    {
      label: "Produced Qty",
      data: props.rows.map(r => r.produced_qty),
      borderColor: "#6366f1",
      backgroundColor: "rgba(99,102,241,0.2)",
      fill: true,
      tension: 0.3,
      pointRadius: 3
    }
  ]
}))

const lineOptions = {
  responsive: true,
  maintainAspectRatio: true,
  plugins: {
    legend: { display: true }
  }
}
</script>
