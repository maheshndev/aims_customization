<template>
	<div class="p-4 bg-white rounded shadow space-y-4">
		<div class="flex flex-wrap items-end justify-between gap-4">
			<div class="flex gap-2">
				<button class="px-3 py-1 rounded bg-blue-100 hover:bg-blue-200" @click="validateCapacity"
					:disabled="!selectedRows.length">
					Validate Capacity
				</button>

				<button class="px-3 py-1 rounded bg-indigo-100 hover:bg-indigo-200" @click="loadPreview"
					:disabled="!selectedRows.length">
					Preview Schedule
				</button>

				<button class="px-3 py-1 rounded bg-green-200 hover:bg-green-300" @click="createWorkOrders"
					:disabled="!selectedRows.length">
					Plan & Create WOs
				</button>
			</div>

			<div class="flex gap-3 text-sm">
				<div>
					<label class="block text-xs text-gray-500">Utilization %</label>
					<input type="number" v-model.number="utilization" min="1" max="100"
						class="border rounded px-2 py-1 w-20" />
				</div>

				<div>
					<label class="block text-xs text-gray-500">Plan Start</label>
					<input type="date" v-model="planStart" class="border rounded px-2 py-1" />
				</div>

				<div>
					<label class="block text-xs text-gray-500">Plan End</label>
					<input type="date" v-model="planEnd" class="border rounded px-2 py-1" />
				</div>
			</div>
		</div>

		<div v-if="!rows.length" class="text-gray-400 text-sm">No items selected</div>

		<div v-else class="overflow-auto">
			<table class="min-w-[1500px] w-full border text-sm">
				<thead class="bg-gray-100 text-xs uppercase">
					<tr>
						<th class="border p-2 text-center">
							<input type="checkbox" v-model="selectAll" @change="toggleAll" />
						</th>
						<th class="border p-2">#</th>
						<th class="border p-2 whitespace-nowrap">Customer</th>
						<th class="border p-2 whitespace-nowrap">Sales Order</th>
						<th class="border p-2 whitespace-nowrap">Item</th>
						<th class="border p-2 whitespace-nowrap">BOM</th>
						<th class="border p-2 whitespace-nowrap">Machine</th>
						<th class="border p-2 whitespace-nowrap">Mould</th>
						<th class="border p-2 whitespace-nowrap text-right">Qty</th>
						<th class="border p-2 whitespace-nowrap text-right">Cycle</th>
						<th class="border p-2 whitespace-nowrap text-right">Cavity</th>
						<th class="border p-2 whitespace-nowrap text-right">Pcs/Hr</th>
						<th class="border p-2 whitespace-nowrap text-right">Req Hrs</th>
						<th class="border p-2 whitespace-nowrap text-right">Avail Hrs</th>
						<th class="border p-2 whitespace-nowrap text-right">Gap</th>
						<th class="border p-2 whitespace-nowrap">Status</th>
						<th class="border p-2 whitespace-nowrap text-center">Preview</th>
					</tr>
				</thead>

				<tbody>
					<template v-for="(r, i) in rows" :key="r.rowKey">
						<tr class="hover:bg-gray-50">
							<td class="border p-2 text-center">
								<input type="checkbox" :value="r.rowKey" v-model="selectedKeys" />
							</td>
							<td class="border p-2 whitespace-nowrap">{{ i + 1 }}</td>
							<td class="border p-2 whitespace-nowrap font-medium">
								{{ r.customer }}
							</td>
							<td class="border p-2 whitespace-nowrap">{{ r.sales_order }}</td>
							<td class="border p-2 whitespace-nowrap">{{ r.item_code }}</td>
							<td class="border p-2 whitespace-nowrap">{{ r.bom_no }}</td>
							<td class="border p-2 whitespace-nowrap">{{ r.machine }}</td>
							<td class="border p-2 whitespace-nowrap">{{ r.mould || "—" }}</td>
							<td class="border p-2 whitespace-nowrap text-right">
								{{ r.schedule_qty }}
							</td>
							<td class="border p-2 whitespace-nowrap text-right">
								{{ r.cycle_time }}
							</td>
							<td class="border p-2 whitespace-nowrap text-right">{{ r.cavity }}</td>
							<td class="border p-2 whitespace-nowrap text-right">
								{{ r.pcs_per_hour }}
							</td>
							<td class="border p-2 whitespace-nowrap text-right">
								{{ r.required_hours }}
							</td>
							<td class="border p-2 whitespace-nowrap text-right">
								{{ r.available_hours }}
							</td>
							<td class="border p-2 whitespace-nowrap text-right">
								{{ r.capacity_gap }}
							</td>

							<td class="border p-2 whitespace-nowrap">
								<span v-if="r.validation_error" class="text-red-600 text-xs">
									{{ r.validation_error }}
								</span>
								<span v-else class="text-green-600 text-xs font-medium"> OK </span>
							</td>

							<td class="border p-2 text-center whitespace-nowrap">
								<button class="px-2 py-0.5 text-xs border rounded bg-gray-50" @click="togglePreview(r)">
									{{ preview[r.rowKey] ? "Hide" : "View" }}
								</button>
							</td>
						</tr>

						<tr v-if="preview[r.rowKey]">
							<td colspan="15" class="bg-gray-50 p-3 whitespace-nowrap">
								<div class="flex flex-wrap gap-2">
									<div v-for="(p, idx) in preview[r.rowKey]" :key="idx"
										class="px-2 py-1 border rounded text-xs bg-white">
										Shift {{ p.shift_no }} → Qty: {{ p.qty }} ({{
											p.planned_hours
										}}
										hrs)
									</div>
								</div>
							</td>
						</tr>
					</template>
				</tbody>
			</table>
		</div>

		<div class="text-sm flex gap-6">
			<div>
				Required Hours: <b>{{ totalRequiredHours }}</b>
			</div>
			<div>
				Selected Rows: <b>{{ selectedRows.length }}</b>
			</div>
		</div>
	</div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from "vue";
import { api } from "../services/api";

const props = defineProps({
	capBoms: { type: Array, default: () => [] },
});

const rows = ref([]);
const preview = ref({});
const selectedKeys = ref([]);
const selectAll = ref(false);
const utilization = ref(90);
const planStart = ref(today());
const planEnd = ref(null);

onMounted(sync);
watch(() => props.capBoms, sync, { deep: true });

function today() {
	return new Date().toISOString().slice(0, 10);
}

function sync() {
	rows.value = props.capBoms.map((b, i) => ({
		...b,
		rowKey: `${b.bom_no}_${b.sales_order}_${i}`,
		schedule_qty: Number(b.required_for_selected_qty || 0),
		machine: b.selected_workstation,
		mould: b.selected_mould || null,
		validation_error: null,
	}));
	preview.value = {};
	selectedKeys.value = [];
}

const selectedRows = computed(() =>
	rows.value.filter((r) => selectedKeys.value.includes(r.rowKey))
);

const totalRequiredHours = computed(() =>
	selectedRows.value.reduce((a, b) => a + Number(b.required_hours || 0), 0).toFixed(2)
);

function toggleAll() {
	selectedKeys.value = selectAll.value ? rows.value.map((r) => r.rowKey) : [];
}

async function validateCapacity() {
	const payload = {
		production_utilization: utilization.value,
		plan_start_date: planStart.value,
		plan_end_date: planEnd.value,
		lines: selectedRows.value.map((r) => ({
			row_key: r.rowKey,
			item_code: r.item_code,
			schedule_qty: r.schedule_qty,
			cycle_time: r.cycle_time,
			cavity: r.cavity,
			machine: r.machine,
			mould: r.mould || null,
			bom_no: r.bom_no,
			sales_order: r.sales_order,
		})),
	};

	const res = await api.validateCapacity(payload);
	const result = res?.data?.message || [];

	const map = Object.fromEntries(result.map((r) => [r.rowKey, r]));

	rows.value = rows.value.map((r) => {
		const v = map[r.rowKey];
		if (!v) return r;

		return {
			...r,
			pcs_per_hour: v.pcs_per_hour,
			required_hours: v.required_hours,
			available_hours: v.available_hours,
			capacity_gap: v.capacity_gap,
			validation_error: v.ok ? null : "Insufficient capacity",
		};
	});
}

async function loadPreview() {
	preview.value = {};

	const payload = {
		production_utilization: utilization.value,
		plan_start_date: planStart.value,
		plan_end_date: planEnd.value,
		lines: selectedRows.value.map((r) => ({
			row_key: r.rowKey,
			item_code: r.item_code,
			schedule_qty: r.schedule_qty,
			machine: r.machine,
			cycle_time: r.cycle_time,
			cavity: r.cavity,
			mould: r.mould,
			bom_no: r.bom_no,
			sales_order: r.sales_order,
		})),
	};

	const res = await api.previewCapacityPlan(payload);

	const list = res?.data?.message || [];

	list.forEach((p) => {
		preview.value[p.row_key] = p.preview;
	});
}

async function togglePreview(row) {
	const payload = {
		production_utilization: utilization.value,
		plan_start_date: planStart.value,
		plan_end_date: planEnd.value,
		lines: [
			{
				row_key: row.rowKey,
				item_code: row.item_code,
				schedule_qty: row.schedule_qty,
				cycle_time: row.cycle_time,
				cavity: row.cavity,
				machine: row.machine,
				mould: row.mould,
				bom_no: row.bom_no,
				sales_order: row.sales_order,
			},
		],
	};

	const res = await api.previewCapacityPlan(payload);
	const list = res?.data.message || [];

	if (list.length) {
		preview.value[row.rowKey] = list[0].preview;
	}
}


async function createWorkOrders() {
	const payload = {
		production_utilization: utilization.value,
		plan_start_date: planStart.value,
		plan_end_date: planEnd.value,
		lines: selectedRows.value.map((r) => ({
			item_code: r.item_code,
			schedule_qty: r.schedule_qty,
			cycle_time: r.cycle_time,
			cavity: r.cavity,
			machine: r.machine,
			mould: r.mould || null,
			bom_no: r.bom_no,
			sales_order: r.sales_order,
		})),
	};

	const res = await api.createWorkOrdersFromMSS(payload);
	frappe.msgprint({
		title: "Successfully Create Work Orders",
		indicator: "green",
		message: `<b>${res.data.message.created_work_orders.length} Work Orders created</b>`,
	});
}
</script>
