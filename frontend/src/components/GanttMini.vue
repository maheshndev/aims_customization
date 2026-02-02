<template>
	<div
		v-if="hasBars"
		class="relative bg-gray-50/50 border border-gray-100/50 rounded-lg overflow-hidden group/gantt"
		:style="{ height: `${containerHeight}px` }"
	>
		<div
			v-for="(bar, index) in positionedBars"
			:key="index"
			class="absolute h-6 rounded-md text-[9px] font-bold text-white px-2 flex items-center whitespace-nowrap shadow-sm transition-all hover:h-7 hover:shadow-md cursor-help z-10"
			:style="getBarStyle(bar)"
			:title="`${bar.label}\n${bar.startStr} - ${bar.endStr}\nDuration: ${Math.round((bar.end - bar.start) / (1000 * 60 * 60 * 24))} days`"
		>
			{{ bar.label }}
		</div>
	</div>

	<div v-else class="text-[10px] text-gray-400 italic font-medium uppercase tracking-tight">
		Timeline unavailable
	</div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
	bars: {
		type: Array,
		default: () => [],
	},
});

/**
 * Normalize & validate bars
 */
const normalizedBars = computed(() =>
	props.bars
		.filter((b) => b?.start && b?.end)
		.map((b) => {
			const s = new Date(b.start);
			const e = new Date(b.end);
			return {
				label: b.label || "",
				start: s.getTime(),
				end: e.getTime(),
				startStr: s.toLocaleDateString(),
				endStr: e.toLocaleDateString(),
			};
		})
		.filter((b) => !isNaN(b.start) && !isNaN(b.end) && b.end > b.start),
);

const hasBars = computed(() => normalizedBars.value.length > 0);

const minTime = computed(() => Math.min(...normalizedBars.value.map((b) => b.start)));

const maxTime = computed(() => Math.max(...normalizedBars.value.map((b) => b.end)));

/**
 * Check if two bars overlap in time
 */
function barsOverlap(bar1, bar2) {
	return bar1.start < bar2.end && bar2.start < bar1.end;
}

/**
 * Assign rows to bars to avoid overlaps
 */
const positionedBars = computed(() => {
	const bars = [...normalizedBars.value];
	const rows = [];

	bars.forEach((bar) => {
		// Find the first row where this bar doesn't overlap with any existing bar
		let rowIndex = 0;
		while (rowIndex < rows.length) {
			const hasOverlap = rows[rowIndex].some((existingBar) => barsOverlap(bar, existingBar));
			if (!hasOverlap) {
				break;
			}
			rowIndex++;
		}

		// Add bar to the found row (or create a new row)
		if (!rows[rowIndex]) {
			rows[rowIndex] = [];
		}
		rows[rowIndex].push(bar);
		bar.row = rowIndex;
	});

	return bars;
});

/**
 * Calculate container height based on number of rows
 */
const containerHeight = computed(() => {
	const maxRow = Math.max(...positionedBars.value.map((b) => b.row || 0));
	return Math.max(40, (maxRow + 1) * 32); // 32px per row (6px bar + 2px padding + 24px spacing)
});

/**
 * Calculate bar style
 */
function getBarStyle(bar) {
	const total = maxTime.value - minTime.value;
	if (total <= 0) return { display: "none" };

	const left = ((bar.start - minTime.value) / total) * 100;
	const width = ((bar.end - bar.start) / total) * 100;
	const top = (bar.row || 0) * 32 + 8; // 32px per row, 8px top padding

	return {
		left: `${left}%`,
		width: `${Math.max(width, 3)}%`,
		top: `${top}px`,
		backgroundColor: bar.label.startsWith("Job")
			? "#6366f1" // Indigo 500
			: "#10b981", // Emerald 500
	};
}
</script>
