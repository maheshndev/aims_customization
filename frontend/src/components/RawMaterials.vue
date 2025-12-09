<template>
	<div class="raw-materials bg-white rounded shadow-sm p-4">
		<div v-if="loading" class="text-gray-500">Loading Raw Materials...</div>
		<div v-if="error" class="text-red-500 mb-2">{{ error }}</div>

		<div v-if="materials.length" class="overflow-x-auto">
			<table class="table-auto w-full border-collapse">
				<thead class="bg-gray-100">
					<tr>
						<th class="border px-3 py-2 text-left">Item</th>
						<th class="border px-3 py-2 text-left">Material</th>
						<th class="border px-3 py-2 text-left">Required Qty</th>
						<th class="border px-3 py-2 text-left">Available Qty</th>
						<th class="border px-3 py-2 text-left">Consumed Qty</th>
					</tr>
				</thead>
				<tbody>
					<tr v-for="rm in materials" :key="rm.name" class="hover:bg-gray-50">
						<td class="border px-3 py-2">{{ rm.item_name }}</td>
						<td class="border px-3 py-2">{{ rm.material_name }}</td>
						<td class="border px-3 py-2">{{ rm.required_qty }}</td>
						<td class="border px-3 py-2">{{ rm.available_qty }}</td>
						<td class="border px-3 py-2">{{ rm.consumed_qty }}</td>
					</tr>
				</tbody>
			</table>
		</div>

		<div v-if="!materials.length && !loading" class="text-gray-500 mt-2">
			No raw materials found.
		</div>
	</div>
</template>

<script>
import axios from "axios";

export default {
	name: "RawMaterials",
	props: { boms: { type: Array, default: () => [] } },
	data() {
		return { materials: [], loading: false, error: null };
	},
	methods: {
		async fetchMaterials() {
			if (!this.boms.length) {
				this.materials = [];
				return;
			}
			this.loading = true;
			this.error = null;
			try {
				const res = await axios.get(
					"/api/method/aims_customization.api.mss_monthly_schedule.get_raw_materials",
					{
						params: { boms: JSON.stringify(this.boms) },
					},
				);
				this.materials = res.data.message || [];
			} catch (err) {
				console.error(err);
				this.error = "Failed to fetch Raw Materials.";
			} finally {
				this.loading = false;
			}
		},
	},
	watch: {
		boms: {
			handler() {
				this.fetchMaterials();
			},
			deep: true,
			immediate: true,
		},
	},
};
</script>
