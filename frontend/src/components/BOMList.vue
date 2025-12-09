<template>
	<div class="bom-list bg-white rounded shadow-sm p-4">
		<div v-if="loading" class="text-gray-500">Loading BOMs...</div>
		<div v-if="error" class="text-red-500 mb-2">{{ error }}</div>

		<div v-if="boms.length" class="overflow-x-auto">
			<table class="table-auto w-full border-collapse">
				<thead class="bg-gray-100">
					<tr>
						<th class="border px-3 py-2 text-left">BOM</th>
						<th class="border px-3 py-2 text-left">Item</th>
						<th class="border px-3 py-2 text-left">Qty</th>
						<th class="border px-3 py-2 text-left">UOM</th>
					</tr>
				</thead>
				<tbody>
					<tr v-for="bom in boms" :key="bom.name" class="hover:bg-gray-50">
						<td class="border px-3 py-2">{{ bom.bom_no }}</td>
						<td class="border px-3 py-2">{{ bom.item_name }}</td>
						<td class="border px-3 py-2">{{ bom.qty }}</td>
						<td class="border px-3 py-2">{{ bom.uom }}</td>
					</tr>
				</tbody>
			</table>
		</div>

		<div v-if="!boms.length && !loading" class="text-gray-500 mt-2">No BOMs found.</div>
	</div>
</template>

<script>
import axios from "axios";

export default {
	name: "BOMList",
	props: { items: { type: Array, default: () => [] } },
	data() {
		return { boms: [], loading: false, error: null };
	},
	methods: {
		async fetchBOMs() {
			if (!this.items.length) {
				this.boms = [];
				return;
			}
			this.loading = true;
			this.error = null;
			try {
				const res = await axios.get(
					"/api/method/aims_customization.api.mss_monthly_schedule.get_boms_for_items",
					{
						params: { items: JSON.stringify(this.items) },
					},
				);
				this.boms = res.data.message || [];
			} catch (err) {
				console.error(err);
				this.error = "Failed to fetch BOMs.";
			} finally {
				this.loading = false;
			}
		},
	},
	watch: {
		items: {
			handler() {
				this.fetchBOMs();
			},
			deep: true,
			immediate: true,
		},
	},
};
</script>
