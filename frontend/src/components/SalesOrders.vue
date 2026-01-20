<template>
	<div class="sales-orders rounded-xl shadow-sm p-2">
		<p class="text-xs text-gray-500">
			System performs monthly machine capacity planning for the selected line.
		</p>
		<div v-if="loading" class="text-gray-500 animate-pulse">Loading Sales Orders...</div>

		<div
			v-if="error"
			class="bg-red-100 text-red-700 px-4 py-2 border border-red-200 rounded mb-4"
		>
			{{ error }}
		</div>

		<div v-if="!loading" class="flex justify-start gap-3 mb-3">
			<button class="px-3 py-1 bg-blue-100 text-black rounded" @click="selectAll">
				Select All
			</button>
			<button class="px-3 py-1 bg-gray-200 text-black rounded" @click="unselectAll">
				Unselect All
			</button>
			<button
				class="px-3 py-1 bg-green-100 text-black rounded hover:bg-green-200"
				@click="refreshOrders"
			>
				🔄 Refresh
			</button>
		</div>

		<div v-if="orders.length && !loading" class="overflow-auto rounded-b-xl">
			<table class="min-w-[1200px] table-auto divide-y divide-gray-200 border">
				<thead class="bg-gray-100 uppercase">
					<tr>
						<th class="px-3 py-2 border">
							<input
								type="checkbox"
								:checked="isAllSelected"
								@change="toggleSelectAll"
							/>
						</th>
						<th class="px-3 py-2 border whitespace-nowrap">#</th>
						<th class="px-3 py-2 border whitespace-nowrap">Sales Order ID</th>
						<th class="px-3 py-2 border whitespace-nowrap">Customer</th>
						<th class="px-3 py-2 border text-right whitespace-nowrap">Total Qty</th>
						<th class="px-3 py-2 border whitespace-nowrap">Month</th>
						<th class="px-3 py-2 border whitespace-nowrap">Transaction</th>
						<th class="px-3 py-2 border whitespace-nowrap">Delivery</th>
						<th class="px-3 py-2 border whitespace-nowrap">Status</th>
						<th class="px-3 py-2 border whitespace-nowrap">Blanket Order ID</th>
					</tr>
				</thead>

				<tbody class="divide-y divide-gray-200">
					<tr
						v-for="(so, index) in orders"
						:key="so.name"
						:class="[
							'hover:bg-gray-50 transition',
							selectedLocal.includes(index) ? 'bg-blue-50' : '',
						]"
					>
						<td class="border px-3 py-2">
							<input type="checkbox" :value="so.name" v-model="selectedLocal" />
						</td>
						<td class="border px-3 py-2 whitespace-nowrap">{{ index + 1 }}</td>
						<td class="border px-3 py-2 whitespace-nowrap">
							<span
								class="cursor-pointer hover:underline hover:text-blue-600"
								@click="OpenSalesOrder(so.name)"
							>
								{{ so.name }}
							</span>
						</td>
						<td class="border px-3 py-2 whitespace-nowrap">{{ so.customer_name }}</td>
						<td class="border px-3 py-2 text-right whitespace-nowrap">
							{{ so.total_qty }}
						</td>
						<td class="border px-3 py-2 whitespace-nowrap">{{ so.month }}</td>
						<td class="border px-3 py-2 whitespace-nowrap">
							{{ so.transaction_date }}
						</td>
						<td class="border px-3 py-2 whitespace-nowrap">{{ so.delivery_date }}</td>
						<td class="border px-3 py-2 whitespace-nowrap">{{ so.status }}</td>
						<td class="border px-3 py-2 whitespace-nowrap">
							{{ so.blanket_order || "" }}
						</td>
					</tr>
				</tbody>
			</table>
		</div>

		<div v-if="!orders.length && !loading" class="text-gray-500 text-center mt-4">
			No Sales Orders found.
		</div>

		<div v-if="fgItems.length" class="mt-6 border-t pt-4 overflow-auto rounded-b-xl">
			<h3 class="font-bold text-lg mb-2">Sales Order Line Items</h3>
			<!-- <button class="px-3 py-1 bg-gray-200 text-black rounded shadow hover:bg-green-300 m-1"
        @click="createMixPlannerBOM">
        Create Planner Mix BOM
      </button> -->

			<table class="min-w-[800px] table-auto divide-y divide-gray-200 border rounded-xl">
				<thead class="bg-gray-100 uppercase">
					<tr>
						<th>Selected</th>
						<th class="px-3 py-2 border whitespace-nowrap">#</th>
						<th class="px-3 py-2 border whitespace-nowrap">Sales Order ID</th>
						<th class="px-3 py-2 border whitespace-nowrap">Item Code</th>
						<th class="px-3 py-2 border whitespace-nowrap">Item Name</th>
						<th class="px-3 py-2 border text-right whitespace-nowrap">Qty</th>
						<th class="px-3 py-2 border whitespace-nowrap">Item Group</th>
						<th class="px-3 py-2 border text-right whitespace-nowrap">Rate</th>
						<th class="px-3 py-2 border whitespace-nowrap">BOM No</th>
						<th class="px-3 py-2 border whitespace-nowrap">Action</th>
					</tr>
				</thead>

				<tbody class="divide-y divide-gray-100">
					<tr
						v-for="(item, index) in fgItems"
						:key="item.item_code"
						class="hover:bg-gray-50"
						:class="[
							'hover:bg-gray-50 transition',
							selectedFGItems.includes(item) ? 'bg-blue-50' : '',
						]"
					>
						<td class="border px-3 py-2">
							<input type="checkbox" :value="item" v-model="selectedFGItems" />
						</td>
						<td class="border px-3 py-2 whitespace-nowrap">{{ index + 1 }}</td>
						<td class="border px-3 py-2 whitespace-nowrap">
							{{ item.sales_order_id }}
						</td>
						<td
							class="border px-3 py-2 whitespace-nowrap"
							:href="`/app/item/${item.item_code}`"
							target="_blank"
						>
							{{ item.item_code }}
						</td>
						<td class="border px-3 py-2 whitespace-nowrap">{{ item.item_name }}</td>
						<td class="border px-3 py-2 text-right whitespace-nowrap">
							{{ item.qty }}
						</td>
						<td class="border px-3 py-2 text-right whitespace-nowrap">
							{{ item.item_group }}
						</td>
						<td class="border px-3 py-2 text-right whitespace-nowrap">
							{{ item.rate }}
						</td>
						<td class="border px-3 py-2 whitespace-nowrap">
							{{ item.bom_no || "No BOM Available Create It" }}
						</td>
						<td class="border px-3 py-2 whitespace-nowrap">
							<span v-if="!item.bom_no">
								<button
									class="px-3 py-1 bg-green-300 text-white-500 rounded shadow hover:bg-white-300 m-1"
									@click="createMixPlannerBOM(item)"
								>
									+ Create Planner Mix BOM
								</button>
							</span>
						</td>
					</tr>
				</tbody>
			</table>
		</div>
	</div>
</template>

<script setup>
import { ref, watch, computed } from "vue";
import { api } from "../services/api";

const props = defineProps({
	boItems: { type: Array, default: () => [] },
	filters: { type: Object, required: true },
});

const emit = defineEmits(["update:selected", "fg-loaded", "so-loaded"]);

const loading = ref(false);
const error = ref(null);
const orders = ref([]);
const selectedLocal = ref([]);
const fgItems = ref([]);
const selectedFGItems = ref([]);

const isAllSelected = computed(
	() => orders.value.length > 0 && selectedLocal.value.length === orders.value.length,
);

const selectAll = () => {
	selectedLocal.value = orders.value.map((o) => o.name);
	processFGItems();
};

const unselectAll = () => {
	selectedLocal.value = [];
	fgItems.value = [];
	emit("fg-loaded", []);
};

const toggleSelectAll = () => (isAllSelected.value ? unselectAll() : selectAll());

const processFGItems = () => {
	const selectedOrders = orders.value.filter((o) => selectedLocal.value.includes(o.name));

	const items = [];
	selectedOrders.forEach((o) => {
		(o.items || []).forEach((it) => {
			items.push({ ...it, sales_order_id: o.name });
		});
	});

	fgItems.value = items;

	emit("fg-loaded", items);
	emit("update:selected", selectedLocal.value);
};

watch(selectedLocal, processFGItems);

const createMixPlannerBOM = (item) => {
	// if (!selectedFGItems.value.length) {
	//   frappe.msgprint("Please select one Finished Good to create a Mix BOM.");
	//   return;
	// }

	// if (selectedFGItems.value.length > 1) {
	//   frappe.msgprint("Please select only ONE FG item to create a Mix BOM.");
	//   return;
	// }

	const fgItem = item.item_code;
	const qty = item.qty || 1;
	const item_group = item.item_group || "";

	let bom_type = "";

	if (item_group === "Finish Good") {
		bom_type = "FG";
	} else if (item_group === "Semi Finish Good") {
		bom_type = "SFG";
	} else {
		bom_type = "";
	}

	const url = `/app/bom/new-bom` + `?item=${fgItem}` + `&bom_type=${bom_type}`;

	window.open(url, "_blank");
};

const OpenSalesOrder = (salesOrderID) => {
	const url = `/app/sales-order/` + salesOrderID;
	window.open(url, "_blank");
};

const fetchOrders = async () => {
	if (!props.filters) {
		return;
	}

	loading.value = true;
	error.value = null;

	try {
		if (props.filters.customer || props.filters.month || props.filters.year) {
			const res = await api.getSalesOrders(
				{
					...props.filters,
				},
				props.boItems,
			);

			orders.value = res.data.message || [];
			selectedLocal.value = [];
			fgItems.value = [];

			emit("so-loaded", orders.value);
		} else {
			orders.value = [];
		}
	} catch (err) {
		console.error(err);
		error.value = "Failed to load Sales Orders.";
	} finally {
		loading.value = false;
	}
};
const refreshOrders = async () => {
	selectedLocal.value = [];
	selectedFGItems.value = [];
	fgItems.value = [];

	await fetchOrders();
};

watch(() => [props.filters, props.boItems], fetchOrders, { immediate: true, deep: true });
</script>
