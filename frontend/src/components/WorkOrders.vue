<template>
	<div class="work-orders rounded shadow-sm p-4 border border-gray-200">
		<h3 class="text-lg font-semibold mb-4 text-gray-800">
			Work Orders ({{ workOrders.length }})
		</h3>

		<div v-if="loading" class="text-gray-500 flex items-center gap-2">
			<svg
				class="animate-spin h-5 w-5 text-blue-500"
				xmlns="http://www.w3.org/2000/svg"
				fill="none"
				viewBox="0 0 24 24"
			>
				<circle
					class="opacity-25"
					cx="12"
					cy="12"
					r="10"
					stroke="currentColor"
					stroke-width="4"
				></circle>
				<path
					class="opacity-75"
					fill="currentColor"
					d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
				></path>
			</svg>
			Loading Work Orders...
		</div>

		<div v-if="error" class="text-red-600 bg-red-100 p-2 rounded mb-2 border border-red-300">
			{{ error }}
		</div>

		<div class="overflow-auto rounded-b-2xl">
			<div class="flex items-center gap-3 mb-3">
				<button
					class="px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600 text-sm"
					@click="selectAll"
				>
					Select All
				</button>

				<button
					class="px-3 py-1 bg-gray-200 text-black rounded hover:bg-gray-300 text-sm"
					@click="unselectAll"
				>
					Unselect All
				</button>

				<button
					class="px-3 py-1 bg-green-500 text-white rounded hover:bg-green-600 text-sm flex items-center gap-1"
					@click="refreshWorkOrders"
				>
					<svg
						xmlns="http://www.w3.org/2000/svg"
						class="h-4 w-4"
						fill="none"
						viewBox="0 0 24 24"
						stroke="currentColor"
						stroke-width="2"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							d="M4 4v5h.582m15.356 2A8.001 8.001 0 004 12a7.961 7.961 0 00-1.565 3.59M18 20v-5h-.582m-15.356-2A8.001 8.001 0 0020 12a7.961 7.961 0 001.565-3.59"
						/>
					</svg>
					Refresh
				</button>

				<span class="text-gray-600 text-sm ml-4">
					Selected: <span class="font-bold">{{ selectedWorkOrders.length }}</span> /
					{{ workOrders.length }}
				</span>
			</div>

			<table class="min-w-[1600px] table-auto w-full border-collapse text-sm">
				<thead class="bg-gray-100 sticky top-0 uppercase">
					<tr>
						<th class="border px-3 py-2 text-left">
							<input
								type="checkbox"
								:checked="isAllSelected"
								@change="toggleSelectAll"
							/>
						</th>
						<th class="border px-3 py-2 text-left whitespace-nowrap">#</th>
						<th class="border px-3 py-2 text-left whitespace-nowrap">Work Order ID</th>
						<th class="border px-3 py-2 text-left whitespace-nowrap">
							Sales Order ID
						</th>
						<th class="border px-3 py-2 text-left whitespace-nowrap">Status</th>
						<th class="border px-3 py-2 text-left whitespace-nowrap">Item Code</th>
						<th class="border px-3 py-2 text-right whitespace-nowrap">
							Work Order Qty
						</th>
						<th class="border px-3 py-2 text-right whitespace-nowrap">Produced Qty</th>
						<th class="border px-3 py-2 text-left whitespace-nowrap">Planned Start</th>
						<th class="border px-3 py-2 text-left whitespace-nowrap">Planned End</th>
						<th class="border px-3 py-2 text-left whitespace-nowrap">Delivery Date</th>
						<th class="border px-3 py-2 text-left whitespace-nowrap">Stock UOM</th>
						<th class="border px-3 py-2 text-left whitespace-nowrap">
							Mat. Transferred
						</th>
						<th class="border px-3 py-2 text-right whitespace-nowrap">
							Disassembled Qty
						</th>
						<th class="border px-3 py-2 text-left whitespace-nowrap">BOM ID</th>
						<th class="border px-3 py-2 text-left whitespace-nowrap">FG Warehouse</th>
						<th class="border px-3 py-2 text-left whitespace-nowrap">
							Scrap Warehouse
						</th>
						<th class="border px-3 py-2 text-left whitespace-nowrap">WIP Warehouse</th>
						<th class="border px-3 py-2 text-left whitespace-nowrap">Mould ID</th>
						<th class="border px-3 py-2 text-left whitespace-nowrap">Company</th>
					</tr>
				</thead>

				<tbody>
					<tr
						v-for="(wo, index) in workOrders"
						:key="wo.wo_name"
						class="transition duration-100"
						:class="statusClass(wo.status)"
					>
						<td class="border px-3 py-2 text-center">
							<input
								type="checkbox"
								:value="wo.wo_name"
								v-model="selectedWorkOrders"
							/>
						</td>
						<td class="border px-3 py-2 whitespace-nowrap">{{ index + 1 }}</td>
						<td class="border px-3 py-2 whitespace-nowrap text-blue-600 font-medium">
							<a
								class="cursor-pointer hover:underline hover:text-blue-600"
								:href="`/app/work-order/${wo.wo_name}`"
								target="_blank"
								>{{ wo.wo_name }}</a
							>
						</td>
						<td class="border px-3 py-2 whitespace-nowrap text-blue-600">
							<a
								class="cursor-pointer hover:underline hover:text-blue-600"
								:href="`/app/sales-order/${wo.so_name}`"
								target="_blank"
								>{{ wo.so_name }}</a
							>
						</td>
						<td class="border px-3 py-2 whitespace-nowrap font-medium">
							{{ wo.status }}
						</td>
						<td class="border px-3 py-2 whitespace-nowrap">
							{{ wo.production_item }}
						</td>
						<td class="border px-3 py-2 whitespace-nowrap text-right">
							{{ wo.wo_qty }}
						</td>
						<td class="border px-3 py-2 whitespace-nowrap text-right">
							{{ wo.produced_qty }}
						</td>
						<td class="border px-3 py-2 whitespace-nowrap">
							{{ wo.planned_start_date }}
						</td>
						<td class="border px-3 py-2 whitespace-nowrap">
							{{ wo.planned_end_date }}
						</td>
						<td class="border px-3 py-2 whitespace-nowrap">
							{{ wo.expected_delivery_date }}
						</td>
						<td class="border px-3 py-2 whitespace-nowrap">{{ wo.stock_uom }}</td>
						<td class="border px-3 py-2 whitespace-nowrap">
							{{ wo.material_transferred_for_manufacturing }}
						</td>
						<td class="border px-3 py-2 whitespace-nowrap text-right">
							{{ wo.disassembled_qty }}
						</td>
						<td class="border px-3 py-2 whitespace-nowrap">{{ wo.bom_no }}</td>
						<td class="border px-3 py-2 whitespace-nowrap">{{ wo.fg_warehouse }}</td>
						<td class="border px-3 py-2 whitespace-nowrap">
							{{ wo.scrap_warehouse }}
						</td>
						<td class="border px-3 py-2 whitespace-nowrap">{{ wo.wip_warehouse }}</td>
						<td class="border px-3 py-2 whitespace-nowrap">{{ wo.mould }}</td>
						<td class="border px-3 py-2 whitespace-nowrap">{{ wo.company }}</td>
					</tr>
				</tbody>
			</table>
		</div>

		<div
			v-if="!workOrders.length && !loading"
			class="text-gray-500 mt-2 p-2 bg-gray-50 rounded"
		>
			No Work Orders found for the selected Sales Orders.
		</div>
	</div>
</template>

<script setup>
import { ref, computed, watch } from "vue";
import { api } from "../services/api";

const props = defineProps({
	salesOrders: {
		type: Array,
		default: () => [],
		validator: (val) =>
			val.every((item) => typeof item === "string" && item.trim().length > 0),
	},
	selected: { type: Array, default: () => [] },
});

const emit = defineEmits(["update:selected"]);
const workOrders = ref([]);
const selectedWorkOrders = ref([]);
const loading = ref(false);
const error = ref(null);

const isAllSelected = computed(
	() =>
		workOrders.value.length > 0 && selectedWorkOrders.value.length === workOrders.value.length,
);

function statusClass(status) {
	if (status === "Completed") return "bg-green-50 hover:bg-green-100";
	if (status === "In Process") return "bg-yellow-50 hover:bg-yellow-100";
	if (status === "Stopped") return "bg-red-50 hover:bg-red-100";
	if (status === "Planned") return "bg-blue-50 hover:bg-blue-100";
	return "hover:bg-gray-100";
}

async function fetchWorkOrders() {
	loading.value = true;
	error.value = null;

	const validSalesOrders = props.salesOrders.filter((so) => so && so.trim());
	if (!validSalesOrders.length) {
		workOrders.value = [];
		selectedWorkOrders.value = [];
		emit("update:selected", []);
		loading.value = false;
		return;
	}

	try {
		const res = await api.getWorkOrders(validSalesOrders);

		workOrders.value = res.data.message || [];

		if (workOrders.value.length > 0) {
			const woNames = workOrders.value.map((wo) => wo.wo_name);
			selectedWorkOrders.value = props.selected.filter((name) => woNames.includes(name));
		} else {
			selectedWorkOrders.value = [];
			emit("update:selected", []);
		}
	} catch (err) {
		console.error("API Error fetching Work Orders:", err);
		error.value = "Failed to fetch Work Orders. Check console for details.";
		workOrders.value = [];
		selectedWorkOrders.value = [];
		emit("update:selected", []);
	} finally {
		loading.value = false;
	}
}

function refreshWorkOrders() {
	selectedWorkOrders.value = [];
	workOrders.value = [];
	fetchWorkOrders();
}

function selectAll() {
	selectedWorkOrders.value = workOrders.value.map((wo) => wo.wo_name);
}

function unselectAll() {
	selectedWorkOrders.value = [];
}

const toggleSelectAll = () => (isAllSelected.value ? unselectAll() : selectAll());

watch(
	selectedWorkOrders,
	(val) => {
		emit("update:selected", [...val]);
	},
	{ deep: true },
);

watch(
	() => props.salesOrders,
	(newVal, oldVal) => {
		const curr = Array.isArray(newVal) ? newVal.filter(Boolean) : [];
		const prev = Array.isArray(oldVal) ? oldVal.filter(Boolean) : [];

		if (JSON.stringify(curr.sort()) === JSON.stringify(prev.sort())) return;

		workOrders.value = [];
		selectedWorkOrders.value = [];
		emit("update:selected", []);

		if (curr.length) {
			fetchWorkOrders();
		}
	},
	{ immediate: true, deep: true },
);
</script>
