<!-- action button create -->
<template>
	<button :class="['action-button', variantClass]" @click="$emit('click')">
		<slot></slot>
	</button>
</template>
<script setup>
defineProps({
	variant: {
		type: String,
		default: "primary", // primary, secondary, danger
	},
});
const variantClass =
	{
		primary: "bg-indigo-600 text-white hover:bg-indigo-700 focus:ring-indigo-500",
		secondary: "bg-gray-200 text-gray-800 hover:bg-gray-300 focus:ring-gray-400",
		danger: "bg-red-600 text-white hover:bg-red-700 focus:ring-red-500",
	}[props.variant] || "bg-indigo-600 text-white hover:bg-indigo-700 focus:ring-indigo-500";
</script>
<style scoped>
.action-button {
	@apply px-4 py-2 rounded-md font-medium focus:outline-none focus:ring-2 focus:ring-offset-2 transition;
}
</style>
