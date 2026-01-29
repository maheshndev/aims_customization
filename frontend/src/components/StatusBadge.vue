<template>
	<span :class="badgeClass" :title="`Current Status: ${status || 'Unknown'}`">
		{{ status || "Unknown" }}
	</span>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
	status: {
		type: String,
		default: "",
	},
});

const badgeClass = computed(() => {
	const base =
		"px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider inline-block shadow-sm";

	switch (props.status) {
		case "Production Completed":
			return `${base} bg-emerald-100 text-emerald-700 border border-emerald-200`;
		case "In Production":
			return `${base} bg-indigo-100 text-indigo-700 border border-indigo-200`;
		case "Planned":
			return `${base} bg-amber-100 text-amber-700 border border-amber-200`;
		default:
			return `${base} bg-slate-100 text-slate-600 border border-slate-200`;
	}
});
</script>
