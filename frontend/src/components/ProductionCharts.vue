<template>
	<div class="grid grid-cols-1 md:grid-cols-2 gap-3 sm:gap-4 mt-4">
		<!-- Quantity Overview -->
		<div class="bg-white p-3 sm:p-4 rounded-xl border border-gray-100 shadow-sm min-h-[300px]">
			<h4
				class="text-[9px] sm:text-[10px] uppercase tracking-wider font-bold text-gray-400 mb-3 sm:mb-4 flex items-center"
			>
				<span class="w-1.5 h-1.5 bg-emerald-500 rounded-full mr-2"></span>
				Quantity Overview
			</h4>
			<div class="h-[200px] flex justify-center">
				<Doughnut :data="qtyData" :options="doughnutOptions" />
			</div>
		</div>

		<!-- Status Breakdown -->
		<div class="bg-white p-3 sm:p-4 rounded-xl border border-gray-100 shadow-sm min-h-[300px]">
			<h4
				class="text-[9px] sm:text-[10px] uppercase tracking-wider font-bold text-gray-400 mb-3 sm:mb-4 flex items-center"
			>
				<span class="w-1.5 h-1.5 bg-amber-500 rounded-full mr-2"></span>
				Status Breakdown
			</h4>
			<div class="h-[200px] flex justify-center">
				<Doughnut :data="statusData" :options="doughnutOptions" />
			</div>
		</div>

		<!-- Progress Distribution (Full Width) -->
		<div
			class="md:col-span-2 bg-white p-3 sm:p-4 rounded-xl border border-gray-100 shadow-sm min-h-[300px]"
		>
			<h4
				class="text-[9px] sm:text-[10px] uppercase tracking-wider font-bold text-gray-400 mb-3 sm:mb-4 flex items-center"
			>
				<span class="w-1.5 h-1.5 bg-blue-500 rounded-full mr-2"></span>
				Production Progress (%)
			</h4>
			<div class="h-[220px]">
				<Bar :data="progressData" :options="barOptions" />
			</div>
		</div>

		<!-- Production Trend (Full Width) -->
		<div
			class="md:col-span-2 bg-white p-3 sm:p-4 rounded-xl border border-gray-100 shadow-sm min-h-[300px]"
		>
			<h4
				class="text-[9px] sm:text-[10px] uppercase tracking-wider font-bold text-gray-400 mb-3 sm:mb-4 flex items-center"
			>
				<span class="w-1.5 h-1.5 bg-indigo-500 rounded-full mr-2"></span>
				Production Trend (Produced Qty)
			</h4>
			<div class="h-[220px]">
				<Line :data="lineData" :options="lineOptions" />
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed } from "vue";
import { Line, Bar, Doughnut } from "vue-chartjs";
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
} from "chart.js";

ChartJS.register(
	BarElement,
	CategoryScale,
	LinearScale,
	ArcElement,
	Tooltip,
	Legend,
	LineElement,
	PointElement,
	Filler,
);

const props = defineProps({
	rows: {
		type: Array,
		default: () => [],
	},
});

// Shared Status Colors
const statusColorsMap = {
	Completed: "#10b981", // Emerald
	"In Production": "#3b82f6", // Blue
	Planned: "#6366f1", // Indigo
	Pending: "#f59e0b", // Amber
	Overdue: "#ef4444", // Red
	Unknown: "#94a3b8", // Slate
};

/* ---------------- BAR ---------------- */
const progressData = computed(() => ({
	labels: props.rows.map((r) => r.item_name || r.item_code),
	datasets: [
		{
			label: "Progress %",
			data: props.rows.map((r) => r.progress),
			backgroundColor: props.rows.map(
				(r) => statusColorsMap[r.status] || statusColorsMap.Unknown,
			),
			borderRadius: 6,
			borderSkipped: false,
		},
	],
}));

const barOptions = {
	responsive: true,
	maintainAspectRatio: false,
	plugins: {
		legend: { display: false }, // Legend redundant for bar chart individual items
		tooltip: {
			callbacks: {
				label: function (context) {
					const row = props.rows[context.dataIndex];
					return `${context.parsed.y}% - ${row.status}`;
				},
				afterLabel: function (context) {
					const row = props.rows[context.dataIndex];
					return `Produced: ${row.produced_qty} / ${row.order_qty}`;
				},
			},
			displayColors: true,
			backgroundColor: "rgba(0, 0, 0, 0.8)",
			titleFont: { size: 11 },
			bodyFont: { size: 10 },
		},
	},
	scales: {
		x: {
			grid: { display: false },
			ticks: {
				font: { size: 9 },
				autoSkip: true,
				maxRotation: 45,
				minRotation: 0,
			},
		},
		y: {
			max: 100,
			beginAtZero: true,
			ticks: { callback: (v) => v + "%", font: { size: 9 } },
			grid: { borderDash: [2, 4] },
		},
	},
};

/* ---------------- DOUGHNUT (Qty) ---------------- */
const qtyData = computed(() => {
	const total = props.rows.reduce((a, r) => a + r.order_qty, 0);
	const produced = props.rows.reduce((a, r) => a + r.produced_qty, 0);

	return {
		labels: ["Produced", "Balance"],
		datasets: [
			{
				label: "Quantity",
				data: [produced, Math.max(total - produced, 0)],
				backgroundColor: ["#10b981", "#f1f5f9"],
				borderWidth: 0,
				hoverOffset: 4,
			},
		],
	};
});

const doughnutOptions = {
	responsive: true,
	maintainAspectRatio: false,
	cutout: "70%",
	plugins: {
		legend: {
			position: "bottom",
			labels: { usePointStyle: true, font: { size: 9 }, boxWidth: 8, padding: 10 },
		},
		tooltip: {
			callbacks: {
				label: function (context) {
					const label = context.label || "";
					const value = context.parsed;
					const total = context.chart._metasets[context.datasetIndex].total;
					const percentage = Math.round((value / total) * 100) + "%";
					return `${label}: ${value} (${percentage})`;
				},
			},
		},
	},
};

/* ---------------- DOUGHNUT (Status) ---------------- */
const statusData = computed(() => {
	const statuses = {};
	props.rows.forEach((r) => {
		const s = r.status || "Unknown";
		statuses[s] = (statuses[s] || 0) + 1;
	});

	return {
		labels: Object.keys(statuses),
		datasets: [
			{
				data: Object.values(statuses),
				backgroundColor: Object.keys(statuses).map(
					(s) => statusColorsMap[s] || statusColorsMap.Unknown,
				),
				borderWidth: 0,
				hoverOffset: 4,
			},
		],
	};
});

/* ---------------- LINE ---------------- */
const lineData = computed(() => ({
	labels: props.rows.map((r) => r.item_name || r.item_code),
	datasets: [
		{
			label: "Produced Qty",
			data: props.rows.map((r) => r.produced_qty),
			borderColor: "#6366f1",
			backgroundColor: "rgba(99,102,241,0.1)",
			fill: true,
			tension: 0.4,
			pointRadius: 4,
			pointHoverRadius: 6,
			borderWidth: 3,
		},
	],
}));

const lineOptions = {
	responsive: true,
	maintainAspectRatio: false,
	plugins: {
		legend: { display: true, labels: { boxWidth: 10, font: { size: 9 } } }, // Enable legend
		tooltip: {
			callbacks: {
				label: function (context) {
					return `Produced: ${context.parsed.y}`;
				},
			},
		},
	},
	scales: {
		x: {
			grid: { display: false },
			ticks: {
				font: { size: 9 },
				autoSkip: true,
				maxRotation: 45,
				minRotation: 0,
			},
		},
		y: {
			beginAtZero: true,
			grid: { borderDash: [2, 4] },
			ticks: { font: { size: 9 } },
		},
	},
};
</script>
