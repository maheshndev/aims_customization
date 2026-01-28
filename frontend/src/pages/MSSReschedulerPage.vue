<template>
	<div class="p-4 sm:p-8 bg-gray-50 min-h-screen font-sans space-y-8">
		<div class="flex items-center justify-between border-b border-gray-200 pb-4 rounded-1xl">
			<div>
				<h2 class="text-2xl font-bold text-gray-900 tracking-tight">
					Work Order Rescheduler
				</h2>
				<p class="text-sm text-gray-500 mt-1">
					Manage and optimize production schedules with ease
				</p>
			</div>
		</div>

		<div
			class="rounded-1xl border border-gray-200 bg-white shadow-sm overflow-hidden transition-all duration-300 hover:shadow-md rounded-sm"
		>
			<WorkOrderRescheduler />
		</div>
	</div>
</template>

<script setup>
import WorkOrderRescheduler from "../components/WorkOrderRescheduler.vue";
</script>

<style lang="scss" scoped></style>
