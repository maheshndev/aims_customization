<template>
	<div
		class="w-full"
		:title="`Produced: ${produced} / Total: ${total} (Remaining: ${total - produced})`"
	>
		<div
			class="flex justify-between text-[10px] font-bold uppercase tracking-tight mb-1 items-center"
		>
			<span class="text-gray-500 tabular-nums">{{ produced }} / {{ total }}</span>
			<span :class="progress >= 100 ? 'text-emerald-500' : 'text-indigo-500'"
				>{{ progress }}%</span
			>
		</div>

		<div
			class="h-1.5 bg-gray-100 rounded-full overflow-hidden shadow-inner border border-gray-50"
		>
			<div
				class="h-full rounded-full transition-all duration-700 ease-in-out shadow-sm"
				:class="progress >= 100 ? 'bg-emerald-500' : 'bg-indigo-500'"
				:style="{ width: progress + '%' }"
			/>
		</div>
	</div>
</template>

<script setup>
defineProps({
	total: {
		type: Number,
		default: 0,
	},
	produced: {
		type: Number,
		default: 0,
	},
	progress: {
		type: Number,
		default: 0,
	},
});
</script>
