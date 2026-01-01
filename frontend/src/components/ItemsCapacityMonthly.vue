<template>
	<div class="p-2 overflow-x-auto rounded-lg shadow-sm">
		<div v-if="loading" class="text-gray-500 animate-pulse">Loading ...</div>

		<div v-if="error" class="bg-red-100 text-red-700 px-4 py-2 border border-red-200 rounded mb-4">
			{{ error }}
		</div>
		<div v-if="rows.length && !loading" class="flex justify-start gap-3 mb-3">
			<button class="px-3 py-1 bg-green-100 text-black rounded hover:bg-green-200" @click="refreshAll">
				🔄 Refresh
			</button>
		</div>
		<div v-if="rows.length && !loading" class="overflow-auto rounded-b-xl">
		<table class="min-w-[1200px] table-auto text-xs border border-gray-300">
			<thead class="bg-gray-100 text-gray-700 uppercase">
				<tr>
					<th class="border px-2 py-1 whitespace-nowrap">#</th>
					<th class="border px-2 py-1 whitespace-nowrap">Customer</th>
					<th class="border px-2 py-1 whitespace-nowrap">Sales Order</th>
					<th class="border px-2 py-1 whitespace-nowrap">Item Name</th>
					<th class="border px-2 py-1 whitespace-nowrap">Schedule Qty</th>
					<th class="border px-2 py-1 whitespace-nowrap">Mould</th>
					<th class="border px-2 py-1 whitespace-nowrap">Cavity</th>
					<th class="border px-2 py-1 whitespace-nowrap">Cycle Time</th>
					<th class="border px-2 py-1 whitespace-nowrap">Machine</th>
					<th class="border px-2 py-1 whitespace-nowrap">Machine Hourly Capacity</th>
					<th class="border px-2 py-1 whitespace-nowrap">Loading Hours</th>
					<th class="border px-2 py-1 whitespace-nowrap">Month Days</th>
					<th class="border px-2 py-1 whitespace-nowrap">Daily Capacity Hrs</th>
					<th class="border px-2 py-1 whitespace-nowrap">Utilization %</th>
				</tr>
			</thead>

			<tbody>
				<tr v-for="(r, index) in rows" :key="`${r.sales_order}-${r.item_code}`" class="hover:bg-gray-50">
					<td class="border px-2 py-1 whitespace-nowrap">{{ index + 1}}</td>
					<td class="border px-2 py-1 whitespace-nowrap">{{ r.customer_name }}</td>
					<td class="border px-2 py-1 whitespace-nowrap">{{ r.sales_order }}</td>
					<td class="border px-2 py-1 whitespace-nowrap">{{ r.item_name }}</td>
					<td class="border px-2 py-1 whitespace-nowrap">{{ r.schedule_qty }}</td>
					<td class="border px-2 py-1 whitespace-nowrap">{{ r.mould }}</td>
					<td class="border px-2 py-1 whitespace-nowrap">{{ r.cavity }}</td>
					<td class="border px-2 py-1 whitespace-nowrap">{{ r.cycle_time }}</td>
					<td class="border px-2 py-1 whitespace-nowrap">{{ r.machine }}</td>
					<td class="border px-2 py-1 whitespace-nowrap">{{ r.machine_hourly_capacity }}</td>
					<td class="border px-2 py-1 whitespace-nowrap">{{ r.loading_hours }}</td>
					<td class="border px-2 py-1 whitespace-nowrap">{{ r.month_days }}</td>
					<td class="border px-2 py-1 whitespace-nowrap">{{ r.daily_capacity_hrs }}</td>
					<td class="border px-2 py-1 whitespace-nowrap">{{ r.utilization }}</td>
				</tr>

				<tr v-if="!rows.length">
					<td colspan="7" class="text-center py-4 text-gray-500">
						No item loading data available
					</td>
				</tr>
			</tbody>
		</table>
		</div>
	</div>
</template>

<script setup>
import { ref, watch } from "vue";
import { api } from "../services/capavityApi";

const props = defineProps({
	filters: { type: Object, required: true }, 
	selectedMachines: { type: Array, required: true }, 
});

const rows = ref([]);
const loading = ref(false);
const error = ref(null);

const loadData = async () => {
	
	
	if (!props.selectedMachines.length) {
		rows.value = [];
		return;
	}

	loading.value = true;
	error.value = null;

	try {
		const res = await api.getItemCapacityMonthly(props.filters, props.selectedMachines);
		rows.value = res?.data?.message || [];
		
	} catch (e) {
		console.error(e);
		error.value = "Failed to load capacity data";
		rows.value = [];
	} finally {
		loading.value = false;
	}
};
const refreshAll = async ()=>{
	rows.value =[];
	await loadData();
}
watch(() => [props.filters, props.selectedMachines], loadData, { deep: true, immediate: true });
</script>
