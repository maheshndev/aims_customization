<template>
	<div class="production-summary  rounded shadow-sm p-4">
		<div v-if="loading" class="text-gray-500">Loading Production Summary...</div>
		<div v-if="error" class="text-red-500 mb-2">{{ error }}</div>

		<div v-if="summary.length" class="overflow-auto rounded-b-2xl">
			<table class="table-auto min-w-[1200px] border-collapse">
				<thead class="bg-gray-100">
					<tr>
						<th class="border px-3 py-2 text-left">Item</th>
						<th class="border px-3 py-2 text-left">Planned Qty</th>
						<th class="border px-3 py-2 text-left">Produced Qty</th>
						<th class="border px-3 py-2 text-left">Pending Qty</th>
					</tr>
				</thead>
				<tbody>
					<tr v-for="item in summary" :key="item.item_code" class="hover:bg-gray-50">
						<td class="border px-3 py-2">{{ item.item_name }}</td>
						<td class="border px-3 py-2">{{ item.planned_qty }}</td>
						<td class="border px-3 py-2">{{ item.produced_qty }}</td>
						<td class="border px-3 py-2">{{ item.pending_qty }}</td>
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
import { api } from "../services/api";

export default {
	name: "ProductionSummary",
	props: { items: { type: Array, default: () => [] } },
	data() {
		return { summary: [], loading: false, error: null };
	},
	methods: {
		async fetchSummary() {
			if (!this.items.length) {
				this.summary = [];
				return;
			}
			this.loading = true;
			this.error = null;
			try {
				const res = api.getProductionStatus()
				this.summary = res.data.message || [];
			} catch (err) {
				console.error(err);
				this.error = "Failed to fetch Production Summary.";
			} finally {
				this.loading = false;
			}
		},
	},
	watch: {
		items: {
			handler() {
				this.fetchSummary();
			},
			deep: true,
			immediate: true,
		},
	},
};
</script>
