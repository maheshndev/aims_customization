<template>
	<div class="raw-materials rounded-xl shadow-sm p-4 bg-white">
		<div v-if="loading" class="text-gray-500 animate-pulse text-center py-4">
			Loading Raw Materials...
		</div>

		<div
			v-if="error"
			class="bg-red-100 text-red-700 px-4 py-2 border border-red-200 rounded mb-4"
		>
			{{ error }}
		</div>

		<div v-if="!loading" class="flex justify-start gap-2 mb-3">
			<button
				class="px-3 py-1 text-sm bg-blue-100 text-black rounded hover:bg-blue-200"
				@click="selectAll"
			>
				Select All
			</button>
			<button
				class="px-3 py-1 text-sm bg-gray-100 text-black rounded hover:bg-gray-200"
				@click="unselectAll"
			>
				Unselect All
			</button>
		</div>

		<div
			v-if="materials.length && !loading"
			class="overflow-auto rounded-lg border border-gray-200 max-h-96"
		>
			<table class="min-w-full table-auto divide-y divide-gray-200">
				<thead class="bg-gray-50 sticky top-0 text-xs text-gray-700 uppercase">
					<tr>
						<th
							class="border px-3 py-2 w-10 text-center sticky left-0 bg-gray-50 z-10"
						>
							<input
								type="checkbox"
								:checked="isAllSelected"
								@change="toggleSelectAll"
							/>
						</th>
						<th class="border px-3 py-2 w-10 text-left whitespace-nowrap">#</th>
						<th class="border px-3 py-2 w-40 text-left whitespace-nowrap">
							Material Code
						</th>
						<th class="border px-3 py-2 w-60 text-left whitespace-nowrap">
							Material Name
						</th>
						<th class="border px-3 py-2 w-20 text-center whitespace-nowrap">UOM</th>
						<th class="border px-3 py-2 w-20 text-center whitespace-nowrap">
							Qty Per Unit
						</th>
						<th class="border px-3 py-2 w-32 text-right whitespace-nowrap">
							Required Qty
						</th>
						<th class="border px-3 py-2 w-32 text-right whitespace-nowrap">
							Qty Percentage %
						</th>
						<th class="border px-3 py-2 w-32 text-right whitespace-nowrap">
							Available Stock
						</th>
						<th class="border px-3 py-2 w-32 text-right whitespace-nowrap">
							Projected Stock
						</th>
						<th class="border px-3 py-2 w-32 text-right whitespace-nowrap">
							Consumed Qty
						</th>
						<th class="border px-3 py-2 w-32 text-right whitespace-nowrap">
							Balance Qty
						</th>
						<th class="border px-3 py-2 w-32 text-center whitespace-nowrap">
							Stock Status
						</th>
						<th class="border px-3 py-2 w-40 text-left whitespace-nowrap">
							Default Warehouse
						</th>
					</tr>
				</thead>

				<tbody class="divide-y divide-gray-100 text-sm">
					<tr
						v-for="(rm, index) in materials"
						:key="rm.rm_item_code"
						class="transition"
						:class="{
							'hover:bg-gray-50': true,
							'bg-blue-50': selectedRows.includes(rm),
						}"
					>
						<td class="border px-3 py-2 text-center sticky left-0 bg-white z-10">
							<input type="checkbox" v-model="selectedRows" :value="rm" />
						</td>
						<td class="border px-3 py-2 whitespace-nowrap">{{ index + 1 }}</td>
						<td class="border px-3 py-2 font-medium whitespace-nowrap">
							{{ rm.rm_item_code }}
						</td>
						<td class="border px-3 py-2 whitespace-nowrap">{{ rm.rm_item_name }}</td>
						<td class="border px-3 py-2 text-center whitespace-nowrap text-xs">
							{{ rm.stock_uom }}
						</td>
						<td class="border px-3 py-2 text-center whitespace-nowrap text-xs">
							{{ rm.qty_per_bom_unit }}
						</td>
						<td
							class="border px-3 py-2 text-right whitespace-nowrap font-semibold text-blue-800"
						>
							{{ rm.total_required_qty }}
						</td>
						<td class="border px-3 py-2 text-center whitespace-nowrap text-xs">
							{{ rm.rm_percentage }}
						</td>
						<td class="border px-3 py-2 text-right whitespace-nowrap">
							{{ rm.available_qty }}
						</td>
						<td class="border px-3 py-2 text-right whitespace-nowrap">
							{{ rm.projected_qty }}
						</td>
						<td class="border px-3 py-2 text-right whitespace-nowrap text-gray-500">
							{{ rm.consumed_qty }}
						</td>
						<td
							class="border px-3 py-2 text-right whitespace-nowrap font-semibold"
							:class="{
								'text-red-600': rm.balance_qty < 0,
								'text-green-600': rm.balance_qty >= 0,
							}"
						>
							{{ rm.balance_qty }}
						</td>
						<td class="border px-3 py-2 text-center whitespace-nowrap">
							<span
								class="px-2 py-0.5 rounded-full text-xs font-medium"
								:class="
									rm.is_sufficient
										? 'bg-green-100 text-green-800'
										: 'bg-red-100 text-red-800'
								"
							>
								{{ rm.is_sufficient ? "Sufficient" : "Shortage" }}
							</span>
						</td>
						<td class="border px-3 py-2 whitespace-nowrap text-xs">
							{{ rm.default_warehouse || "N/A" }}
						</td>
					</tr>
				</tbody>
			</table>
		</div>

		<div v-if="!materials.length && !loading" class="text-gray-500 text-center mt-4 p-2">
			No raw materials calculated. Select BOMs to view requirements.
		</div>
	</div>
</template>

<script setup>
import { ref, watch, computed } from "vue";
import { api } from "../services/api";

const props = defineProps({
	boms: { type: Array, default: () => [] },
	modelValue: { type: Array, default: () => [] },
});

const emit = defineEmits(["update:modelValue", "raw-material-loaded"]);

const materials = ref([]);
const selectedRows = ref([]);
const loading = ref(false);
const error = ref(null);

const isAllSelected = computed(
	() => materials.value.length && selectedRows.value.length === materials.value.length
);

const selectAll = () => {
	selectedRows.value = materials.value.slice();
};
const unselectAll = () => {
	selectedRows.value = [];
};
const toggleSelectAll = () => (isAllSelected.value ? unselectAll() : selectAll());

const fetchMaterials = async () => {
	if (!props.boms.length) {
		materials.value = [];
		selectedRows.value = [];
		emit("update:modelValue", []);
		emit("raw-material-loaded", []);
		return;
	}

	loading.value = true;
	error.value = null;

	try {
		const payload = props.boms.map((bom) => ({
			bom_no: bom.bom_no,
			required_for_selected_qty: bom.required_for_selected_qty,
		}));
		const res = await api.getRawMaterialsForBOMs(payload);

		materials.value = res.data.message || [];

		selectedRows.value = materials.value.slice();

		emit("raw-material-loaded", materials.value);
	} catch (err) {
		console.error("Raw Material Fetch Error:", err);
		error.value = err.message || "Failed to fetch Raw Materials.";
	} finally {
		loading.value = false;
	}
};

watch(() => props.boms, fetchMaterials, { deep: true, immediate: true });

watch(
	selectedRows,
	(newSelection) => {
		emit("update:modelValue", newSelection);
	},
	{ deep: true }
);

watch(
	() => props.modelValue,
	(newModelValue) => {
		if (!newModelValue) return;

		const currentCodes = selectedRows.value
			.map((item) => item.rm_item_code)
			.sort()
			.join(",");
		const newCodes = newModelValue
			.map((item) => item.rm_item_code)
			.sort()
			.join(",");

		if (currentCodes !== newCodes) {
			const existingMaterials = newModelValue.filter((item) =>
				materials.value.some((m) => m.rm_item_code === item.rm_item_code)
			);
			selectedRows.value = existingMaterials.slice();
		}
	},
	{ deep: true, immediate: true }
);
</script>

<style scoped>
.sticky {
	position: sticky;
}

.left-0 {
	left: 0;
}
</style>
