<template>
  <div class="production-summary rounded-xl shadow-sm p-4 bg-white">
    <!-- Loading -->
    <div v-if="loading" class="text-gray-500">Loading Production Summary...</div>
    <!-- Error -->
    <div v-if="error" class="text-red-500 mb-2">{{ error }}</div>

    <!-- Chart -->
    <canvas v-if="summary.length" ref="chart" class="mb-6"></canvas>

    <!-- Table -->
    <div v-if="summary.length" class="overflow-auto rounded-b-2xl">
      <table class="table-auto min-w-[1200px] border-collapse">
        <thead class="bg-gray-100">
          <tr>
            <th class="border px-3 py-2">#</th>
            <th class="border px-3 py-2">Item</th>
            <th class="border px-3 py-2">Planned Qty</th>
            <th class="border px-3 py-2">Produced Qty</th>
            <th class="border px-3 py-2">Pending Qty</th>
            <th class="border px-3 py-2">WIP Qty</th>
            <th class="border px-3 py-2">Stock Qty</th>
            <th class="border px-3 py-2">Dispatched Qty</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(item, index) in summary" :key="item.item_code" class="hover:bg-gray-50">
            <td class="border px-3 py-2">{{ index + 1 }}</td>
            <td class="border px-3 py-2">{{ item.item_name }}</td>
            <td class="border px-3 py-2">{{ item.planned_qty }}</td>
            <td class="border px-3 py-2">{{ item.produced_qty }}</td>
            <td class="border px-3 py-2">{{ item.pending_qty }}</td>
            <td class="border px-3 py-2">{{ item.wip_qty }}</td>
            <td class="border px-3 py-2">{{ item.available_stock }}</td>
            <td class="border px-3 py-2">{{ item.dispatched_qty }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="!summary.length && !loading" class="text-gray-500 mt-2">
      No production data available.
    </div>
  </div>
</template>

<script>
import { Chart, registerables } from "chart.js";
Chart.register(...registerables);
import { api } from "../services/api";

export default {
  name: "ProductionSummary",
  props: { 
    filters: { type: Object, required: true }, // { customer, month, year }
    jobCards: { type: Array, default: () => [] }
  },
  data() {
    return {
      summary: [],
      loading: false,
      error: null,
      chart: null
    };
  },
  methods: {
    async fetchSummary() {
      const { customer, month, year } = this.filters || {};
      if (!customer || !month || !year) return;

      this.loading = true;
      this.error = null;

      try {
        const res = await api.getProductionSummary(customer, month, year);
        this.summary = res.data.message || [];
        this.renderChart();
      } catch (err) {
        console.error(err);
        this.error = "Failed to fetch Production Summary.";
      } finally {
        this.loading = false;
      }
    },
    renderChart() {
      if (!this.summary.length) return;

      const labels = this.summary.map(i => i.item_name);
      const planned = this.summary.map(i => i.planned_qty);
      const produced = this.summary.map(i => i.produced_qty);
      const pending = this.summary.map(i => i.pending_qty);

      if (this.chart) this.chart.destroy();

      const ctx = this.$refs.chart.getContext("2d");
      this.chart = new Chart(ctx, {
        type: "bar",
        data: {
          labels,
          datasets: [
            { label: "Planned", data: planned, backgroundColor: "rgba(59,130,246,0.6)" },
            { label: "Produced", data: produced, backgroundColor: "rgba(16,185,129,0.6)" },
            { label: "Pending", data: pending, backgroundColor: "rgba(251,191,36,0.6)" }
          ]
        },
        options: {
          responsive: true,
          plugins: {
            legend: { position: "top" },
            tooltip: { mode: "index", intersect: false }
          },
          scales: {
            x: { stacked: true },
            y: { stacked: false, beginAtZero: true }
          }
        }
      });
    }
  },
  watch: {
    filters: {
      handler() { this.fetchSummary(); },
      deep: true,
      immediate: true
    }
  },
  mounted() {
    this.fetchSummary();
  }
};
</script>

<style>
.production-summary table th,
.production-summary table td {
  text-align: center;
}
</style>
