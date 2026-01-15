<template>
	<div class="p-4 bg-white rounded shadow space-y-4">
		<div class="flex flex-wrap items-center justify-between gap-4">
			<div class="flex gap-2">
				<button class="px-3 py-1 rounded bg-blue-100 hover:bg-blue-200" @click="openModal('validate')"
					:disabled="!selectedRows.length || hasValidationErrors">
					Validate Capacity
				</button>



				<button class="px-3 py-1 rounded bg-green-200 hover:bg-green-300" @click="openModal('create')"
					:disabled="!selectedRows.length || hasValidationErrors">
					+ Plan & Create WOs
				</button>
			</div>
		</div>

        <!-- Scheduling Modal -->
		<div v-if="showModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
			<div class="bg-white rounded p-6 shadow-xl max-w-5xl w-full mx-4 space-y-4">
				<h3 class="font-bold text-lg border-b pb-2">
					{{ modalTitle }}
				</h3>
				
				<!-- Input Fields in 3 Columns -->
				<div class="grid grid-cols-3 gap-4">
					<!-- Column 1 -->
					<div>
						<label class="block text-xs text-gray-500 mb-1">Utilization %</label>
						<input type="number" v-model.number="utilization" min="1" max="100" class="border rounded px-2 py-1 w-full" />
					</div>

					<!-- Column 2 -->
					<div>
						<label class="block text-xs text-gray-500 mb-1">Plan Start Date</label>
						<input type="date" v-model="planStartWrapper" class="border rounded px-2 py-1 w-full" />
					</div>

					<!-- Column 3 -->
					<div>
						<label class="block text-xs text-gray-500 mb-1">Plan Start Time</label>
						<input type="time" v-model="planStartTime" class="border rounded px-2 py-1 w-full" />
					</div>

					<!-- Column 1 (Row 2) -->
					<div>
						<label class="block text-xs text-gray-500 mb-1">Plan End Date</label>
						<input type="date" v-model="planEnd" class="border rounded px-2 py-1 w-full" />
					</div>

					<!-- Column 2 (Row 2) - Action Buttons -->
					<div class="flex gap-2 items-end">
						<button class="px-3 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200 flex-1"
							@click="checkAvailability">
							Check Availability
						</button>
					</div>

					<!-- Column 3 (Row 2) - Refresh Button -->
					<div class="flex items-end">
						<button class="px-3 py-1 bg-gray-100 text-gray-700 rounded hover:bg-gray-200 w-full"
							@click="refreshData">
							Refresh
						</button>
					</div>
				</div>
				
				<!-- Availability Table -->
				<div v-if="schedulePreview.length" class="mt-4 border rounded overflow-hidden max-h-80 overflow-y-auto">
					<table class="min-w-full text-xs text-left">
						<thead class="bg-gray-50 font-medium text-gray-700 sticky top-0">
							<tr>
								<th class="px-3 py-2">Item</th>
								<th class="px-3 py-2">Machine</th>
								<th class="px-3 py-2">Mould</th>
								<th class="px-3 py-2">Available From</th>
								<th class="px-3 py-2">Status</th>
							</tr>
						</thead>
						<tbody class="divide-y divide-gray-100">
							<tr v-for="row in schedulePreview" :key="row.row_key"
								:class="{
									'bg-green-50': row.is_available,
									'bg-yellow-50': !row.is_available
								}">
								<td class="px-3 py-2">{{ row.item_code }}</td>
								<td class="px-3 py-2">{{ row.machine }}</td>
								<td class="px-3 py-2">{{ row.mould || '-' }}</td>
								<td class="px-3 py-2 font-mono text-blue-600">
									{{ row.available_start && row.available_start.split(' ')[0] }} 
									<span class="text-gray-500">{{ row.available_start && row.available_start.split(' ')[1] }}</span>
								</td>
								<td class="px-3 py-2" :class="{
									'text-green-600 font-medium': row.is_available,
									'text-orange-600': !row.is_available
								}">{{ row.reason }}</td>
							</tr>
						</tbody>
					</table>
				</div>

				<div class="flex justify-end gap-2 pt-2 border-t mt-6">
					<button @click="closeModal" class="px-3 py-1 bg-gray-100 hover:bg-gray-200 rounded">
						Cancel
					</button>
					<button @click="confirmAction" class="px-3 py-1 bg-blue-600 text-white hover:bg-blue-700 rounded">
						Proceed
					</button>
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
						<th class="border p-2 whitespace-nowrap">SO Item Code</th>
						<th class="border p-2 whitespace-nowrap">BOM</th>
						<th class="border p-2 whitespace-nowrap">Machine</th>
						<th class="border p-2 whitespace-nowrap">Mould</th>
						<th class="border p-2 whitespace-nowrap text-right">Schedule Qty</th>
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
						<tr class="hover:bg-gray-50" :class="{
							'bg-red-50': r.validation_error,
							'bg-green-50': !r.validation_error && r.required_hours,
						}">
							<td class="border p-2 text-center">
								<input type="checkbox" :value="r.rowKey" v-model="selectedKeys" />
							</td>
							<td class="border p-2 whitespace-nowrap">{{ i + 1 }}</td>
							<td class="border p-2 whitespace-nowrap font-medium">
								{{ r.customer }}
							</td>
							<td class="border p-2 whitespace-nowrap">{{ r.sales_order }}</td>
							<td class="border p-2 whitespace-nowrap relative group cursor-pointer">
								{{ r.item_code }}
								<!-- Tooltip -->
								<div
									class="absolute left-1/2 transform -translate-x-1/2 -top-8 bg-gray-800 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap">
									{{ r.item_name }}
								</div>
							</td>
							<td class="border p-2 whitespace-nowrap">{{ r.bom_no }}</td>
							<td class="border p-2 whitespace-nowrap">{{ r.machine }}</td>
							<td class="border p-2 whitespace-nowrap relative group cursor-pointer">
								{{ r.mould || "—" }}
								<!-- Tooltip -->
								<div
									class="absolute left-1/2 transform -translate-x-1/2 -top-8 bg-gray-800 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap">
									{{ r.mould_name }}
								</div>
							</td>
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
	rawMaterials: { type: Array, default: () => [] },
});

const emit = defineEmits(['refresh', 'message']);

const rows = ref([]);
const preview = ref({});
const selectedKeys = ref([]);
const selectAll = ref(false);
const utilization = ref(90);
// planStart: Date string YYYY-MM-DD
const planStart = ref(today());
// planStartTime: Time string HH:mm
const planStartTime = ref("06:00");
const planEnd = ref(null);

const showModal = ref(false);
const modalAction = ref(null);
const schedulePreview = ref([]);

const planStartWrapper = computed({
	get: () => planStart.value,
	set: (val) => { planStart.value = val; }
});

const modalTitle = computed(() => {
	if (modalAction.value === 'validate') return 'Validate Capacity';
	if (modalAction.value === 'create') return 'Plan & Create Work Orders';
	return 'Capacity Planning';
});

function openModal(action) {
	modalAction.value = action;
	showModal.value = true;
	schedulePreview.value = []; // Reset on open
}

function closeModal() {
	showModal.value = false;
	modalAction.value = null;
	schedulePreview.value = []; // Reset on close
}

function refreshData() {
    // Clear previous results
    schedulePreview.value = [];
    rows.value.forEach(r => {
        r.validation_error = null;
        r.capacity_gap = null;
        r.available_hours = null;
        r.required_hours = null;
        r.pcs_per_hour = null;
    });
    preview.value = {};
    
    // Re-trigger validation or check availability if inputs are valid
    if (validateInputs()) {
        if (modalAction.value === 'validate') {
             validateCapacity();
        } else {
             checkAvailability();
        }
        showMessage({ title: "Refreshed", message: "Data refreshed based on new inputs.", indicator: "green" });
    }
}

function confirmAction() {
    if (!validateInputs()) return;
    
	if (modalAction.value === 'validate') validateCapacity();
	else if (modalAction.value === 'create') createWorkOrders();
	closeModal();
}

function validateInputs() {
    if (utilization.value <= 0 || utilization.value > 100) {
        showMessage({ title: "Validation Error", message: "Utilization must be between 1 and 100%", indicator: "red" });
        return false;
    }
    if (!planEnd.value) {
        showMessage({ title: "Validation Error", message: "Plan End Date is required", indicator: "red" });
        return false;
    }
    if (new Date(planEnd.value) < new Date(planStart.value)) {
        showMessage({ title: "Validation Error", message: "Plan End Date cannot be before Plan Start Date", indicator: "red" });
        return false;
    }
    return true;
}

async function checkAvailability() {
	if (!selectedRows.value.length) {
        showMessage({ title: "Validation Error", message: "Please select at least one order", indicator: "orange" });
        return;
    }
    if (!planStart.value) {
        showMessage({ title: "Validation Error", message: "Plan Start Date is required", indicator: "orange" });
        return;
    }
	try {
        const lines = selectedRows.value.map(r => ({
           rowKey: r.rowKey,
           item_code: r.item_code,
           machine: r.machine,
           mould: r.mould
        }));
        
		const res = await api.getSmartSchedulePreview(JSON.stringify(lines), planStart.value, planEnd.value);
		schedulePreview.value = res.data.message || [];
        
        // Auto-set Plan Start to the LATEST available start time found
        let maxDt = null;
        let maxTime = null;
        
        schedulePreview.value.forEach(p => {
            if (p.available_start) {
                const dt = new Date(p.available_start);
                if (!maxDt || dt > maxDt) {
                    maxDt = dt;
                    // Format time HH:mm
                    const hrs = String(dt.getHours()).padStart(2, '0');
                    const mins = String(dt.getMinutes()).padStart(2, '0');
                    maxTime = `${hrs}:${mins}`;
                }
            }
        });
        
        if (maxDt) {
            // YYYY-MM-DD
            const yyyy = maxDt.getFullYear();
            const mm = String(maxDt.getMonth() + 1).padStart(2, '0');
            const dd = String(maxDt.getDate()).padStart(2, '0');
            
            planStart.value = `${yyyy}-${mm}-${dd}`;
            planStartTime.value = maxTime || "06:00";
            
            showMessage({
                title: "Availability Checked",
                message: `Plan Start updated to optimum availability: ${planStart.value} ${planStartTime.value}`,
                indicator: "green"
            });
        }
	} catch (e) {
		console.error(e);
        // Error handling fallback
        const msg = e.message || "Failed to check availability";
		showMessage({ title: "Error", message: msg, indicator: "red" });
	}
}

onMounted(sync);
watch(() => props.capBoms, sync, { deep: true });
watch(() => props.rawMaterials, sync, { deep: true });

function today() {
	return new Date().toISOString().slice(0, 10);
}

function sync() {
	const rms = props.rawMaterials || [];

	rows.value = props.capBoms
        // 2. Filter out items that already have Work Orders
        .filter(b => !b.has_work_order)
        .map((b, i) => {
            // 3. Inject updated Raw Materials (percentages/qtys) filtered for this specific SO + BOM
            const lineRMs = rms.filter(r => r.sales_order === b.sales_order && r.bom_no === b.bom_no)
                               .map(r => ({
                                   item_code: r.rm_item_code,
                                   base_rm_percentage: r.base_rm_percentage,
                                   adjustable_rm_percentage: r.adjustable_rm_percentage,
                                   total_adjusted_qty: r.required_qty,
                                   total_base_qty: r.base_required_qty,
                               }));

            return {
                ...b,
                rowKey: `${b.bom_no}_${b.sales_order}_${i}`,
                schedule_qty: Number(b.required_for_selected_qty || 0),
                machine: b.selected_workstation,
                mould: b.selected_mould || null,
                raw_materials: lineRMs,
                validation_error: null,
            };
        });
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
function showMessage({ title = "Message", message = "", indicator = "blue" }) {
	frappe.msgprint({
		title,
		message: message || "—",
		indicator, // green | red | orange | blue
	});
}

function extractFrappeError(err) {
	// Frappe thrown error
	if (err?.response?.data?._server_messages) {
		try {
			const msgs = JSON.parse(err.response.data._server_messages);
			return msgs.join("<br>");
		} catch {
			return err.response.data._server_messages;
		}
	}

	// Validation error (custom raise)
	if (err?.response?.data?.message) {
		return err.response.data.message;
	}

	// Axios network error
	if (err?.message) {
		return err.message;
	}

	return "Unexpected server error";
}
const hasValidationErrors = computed(() =>
	selectedRows.value.some(r => r.validation_error)
);


async function validateCapacity(customLines = null) {
	try {
		const targetLines = customLines || selectedRows.value;

		if (!targetLines.length) {
			if (!customLines) {
				showMessage({
					title: "Selection Needed",
					message: "Please select lines to validate capacity",
					indicator: "orange",
				});
			}
			return;
		}

		const payload = {
			production_utilization: utilization.value,
			plan_start_date: planStart.value,
			plan_start_time: planStartTime.value,
			plan_end_date: planEnd.value,
			lines: targetLines.map((r) => ({
				row_key: r.rowKey,
				item_code: r.item_code,
				schedule_qty: r.schedule_qty,
				cycle_time: r.cycle_time,
				cavity: r.cavity,
				machine: r.machine,
				mould: r.mould || null,
				bom_no: r.bom_no,
				raw_materials: r.raw_materials,
				sales_order: r.sales_order,
			})),
		};

		const res = await api.validateCapacity(payload);
		const result = res?.data?.message || [];

		if (!result.length) {
			showMessage({
				title: "No Data",
				message: "No capacity data returned from server",
				indicator: "orange",
			});
			return;
		}

		const map = Object.fromEntries(result.map((r) => [r.rowKey, r]));

		let errorCount = 0;

		rows.value = rows.value.map((r) => {
			const v = map[r.rowKey];
			if (!v) return r;

			if (!v.ok) errorCount++;

			return {
				...r,
				pcs_per_hour: v.pcs_per_hour,
				required_hours: v.required_hours,
				available_hours: v.available_hours,
				capacity_gap: v.capacity_gap,
				validation_error: v.ok ? null : v.error || "Insufficient capacity",
			};
		});

		showMessage({
			title: "Capacity Validation",
			message:
				errorCount > 0
					? `${errorCount} line(s) have insufficient capacity`
					: "All selected lines passed capacity validation",
			indicator: errorCount > 0 ? "orange" : "green",
		});
	} catch (err) {
		showMessage({
			title: "Validation Failed",
			message: extractFrappeError(err),
			indicator: "red",
		});
	}
}

async function loadPreview() {
	try {
		preview.value = {};

		const payload = {
			production_utilization: utilization.value,
			plan_start_date: planStart.value,
            plan_start_time: planStartTime.value,
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
				raw_materials: r.raw_materials,
				sales_order: r.sales_order,
			})),
		};

		const res = await api.previewCapacityPlan(payload);
		const list = res?.data?.message || [];

		if (!list.length) {
			showMessage({
				title: "Preview",
				message: "No preview schedule generated",
				indicator: "orange",
			});
			return;
		}

		list.forEach((p) => {
			preview.value[p.row_key] = p.preview || [];

			if (p.error) {
				showMessage({
					title: "Preview Warning",
					message: p.error,
					indicator: "orange",
				});
			}
		});

		showMessage({
			title: "Preview Generated",
			message: "Production schedule preview generated successfully",
			indicator: "green",
		});
	} catch (err) {
		showMessage({
			title: "Preview Failed",
			message: extractFrappeError(err),
			indicator: "red",
		});
	}
}

async function togglePreview(row) {
	if (preview.value[row.rowKey]) {
		preview.value[row.rowKey] = null;
		return;
	}

	const payload = {
		production_utilization: utilization.value,
		plan_start_date: planStart.value,
		plan_start_time: planStartTime.value,
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
				raw_materials: row.raw_materials,
				sales_order: row.sales_order,
			},
		],
	};

	try {
		const res = await api.previewCapacityPlan(payload);
		const list = res?.data?.message || [];

		if (list.length) {
			preview.value[row.rowKey] = list[0].preview || [];
		}
	} catch (err) {
		showMessage({
			title: "Preview Error",
			message: extractFrappeError(err),
			indicator: "red",
		});
	}
}

async function createWorkOrders() {
	try {
		const payload = {
			production_utilization: utilization.value,
			plan_start_date: planStart.value,
            plan_start_time: planStartTime.value,
			plan_end_date: planEnd.value,
			lines: selectedRows.value.map((r) => ({
				item_code: r.item_code,
				schedule_qty: r.schedule_qty,
				cycle_time: r.cycle_time,
				cavity: r.cavity,
				machine: r.machine,
				mould: r.mould || null,
				bom_no: r.bom_no,
				raw_materials: r.raw_materials,
				sales_order: r.sales_order,
			})),
		};

		const res = await api.createWorkOrdersFromMSS(payload);
		const msg = res?.data?.message || {};

		let html = "";

		if (msg.created_work_orders?.length) {
			html += `<p class="text-green-600">
				<b>${msg.created_work_orders.length}</b> Work Orders created
			</p>`;
		}

		if (msg.already_exists?.length) {
			html += `<p class="text-orange-600 mt-2">
				<b>Already Exists:</b><br>
				${msg.already_exists.join("<br>")}
			</p>`;
		}

		if (msg.failed?.length) {
			html += `<p class="text-red-600 mt-2">
				<b>Failed:</b><br>
				${msg.failed.join("<br>")}
			</p>`;
		}

		showMessage({
			title: "Work Order Creation Summary",
			message: html || "No work orders were created",
			indicator: msg.failed?.length
				? "red"
				: msg.already_exists?.length
					? "orange"
					: "green",
		});
	} catch (err) {
		showMessage({
			title: "Work Order Creation Failed",
			message: extractFrappeError(err),
			indicator: "red",
		});
	}
}
</script>
