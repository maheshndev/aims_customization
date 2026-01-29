<template>
	<div
		v-if="hasBars"
		class="relative h-10 bg-gray-50/50 border border-gray-100/50 rounded-lg overflow-hidden group/gantt"
	>
		<div
			v-for="(bar, index) in normalizedBars"
			:key="index"
			class="absolute h-6 top-2 rounded-md text-[9px] font-bold text-white px-2 flex items-center whitespace-nowrap shadow-sm transition-all hover:h-7 hover:top-1.5 hover:shadow-md cursor-help z-10"
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
 * Calculate bar style
 */
function getBarStyle(bar) {
	const total = maxTime.value - minTime.value;
	if (total <= 0) return { display: "none" };

	const left = ((bar.start - minTime.value) / total) * 100;
	const width = ((bar.end - bar.start) / total) * 100;

	return {
		left: `${left}%`,
		width: `${Math.max(width, 3)}%`,
		backgroundColor: bar.label.startsWith("Job")
			? "#6366f1" // Indigo 500
			: "#10b981", // Emerald 500
	};
}
</script>
