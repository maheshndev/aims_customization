<template>
	<div class="space-y-3 sm:space-y-4">
		<!-- Header Section -->
		<div
			class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-white p-2.5 sm:p-3 rounded-xl border border-gray-100 shadow-sm"
		>
			<div class="text-center sm:text-left">
				<h2
					class="text-base sm:text-lg font-bold text-gray-800 flex items-center justify-center sm:justify-start"
				>
					<span class="w-1.5 h-5 bg-blue-600 rounded-full mr-2 hidden sm:block"></span>
					Production Summary
				</h2>
				<p class="text-[9px] sm:text-[10px] text-gray-400 mt-0.5 sm:ml-3.5">
					Real-time production oversight and progress tracking
				</p>
			</div>
			<div class="flex items-center justify-center sm:justify-end gap-2">
				<button
					@click="refresh"
					:disabled="loading"
					class="flex items-center gap-1.5 sm:gap-2 px-3 py-1.5 text-[10px] sm:text-xs font-semibold rounded-lg border border-gray-200 bg-white text-gray-700 hover:bg-gray-50 hover:border-gray-300 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-sm active:scale-95"
				>
					<span :class="{ 'animate-spin': loading }">🔄</span>
					{{ loading ? "Updating..." : "Refresh" }}
				</button>
			</div>
		</div>

		<!-- KPI Grid -->
		<div class="grid grid-cols-2 lg:grid-cols-4 xl:grid-cols-4 gap-2 sm:gap-3">
			<Kpi label="Total Orders" :value="rows.length" />
			<Kpi label="Total Qty" :value="totalQty.toLocaleString()" />
			<Kpi label="Produced" :value="totalProduced.toLocaleString()" />
			<Kpi label="Avg Completion" :value="avgProgress + '%'" />
		</div>

		<!-- Table Section -->
		<div class="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
			<div class="overflow-x-auto">
				<table class="w-full text-left border-collapse min-w-[1000px]">
					<thead>
						<tr class="bg-gray-50/50 border-b border-gray-100">
							<th
								class="px-2 py-2 text-[10px] font-bold uppercase tracking-wider text-gray-400 w-10 text-center"
							>
								#
							</th>
							<th
								class="px-2 py-2 text-[10px] font-bold uppercase tracking-wider text-gray-400"
							>
								Item Details
							</th>
							<th
								class="px-2 py-2 text-[10px] font-bold uppercase tracking-wider text-gray-400 text-right"
							>
								Order
							</th>
							<th
								class="px-2 py-2 text-[10px] font-bold uppercase tracking-wider text-gray-400 text-right"
							>
								Produced
							</th>
							<th
								class="px-2 py-2 text-[10px] font-bold uppercase tracking-wider text-gray-400 text-right"
							>
								Balance
							</th>
							<th
								class="px-2 py-2 text-[10px] font-bold uppercase tracking-wider text-gray-400 min-w-[150px]"
							>
								Progress
							</th>
							<th
								class="px-2 py-2 text-[10px] font-bold uppercase tracking-wider text-gray-400"
							>
								Status
							</th>
							<th
								class="px-2 py-2 text-[10px] font-bold uppercase tracking-wider text-gray-400 min-w-[200px]"
							>
								Timeline
							</th>
							<th
								class="px-2 py-2 text-[10px] font-bold uppercase tracking-wider text-gray-400 min-w-[200px]"
							>
								Job Card Timeline
							</th>
						</tr>
					</thead>

					<tbody class="divide-y divide-gray-50">
						<template v-if="loading && !rows.length">
							<tr v-for="i in 3" :key="i">
								<td colspan="9" class="px-3 py-6 animate-pulse">
									<div class="h-3 bg-gray-50 rounded w-full"></div>
								</td>
							</tr>
						</template>

						<template v-else-if="!rows.length">
							<tr>
								<td colspan="9" class="px-3 py-16 text-center">
									<div class="flex flex-col items-center">
										<span class="text-3xl mb-2">📋</span>
										<p class="text-xs text-gray-400 font-medium">
											No results found.
										</p>
									</div>
								</td>
							</tr>
						</template>

						<template v-else>
							<tr
								v-for="(r, index) in rows"
								:key="r.item_code"
								class="hover:bg-blue-50/20 transition-colors group"
							>
								<td
									class="px-2 py-2 text-[10px] font-bold text-gray-400 text-center bg-gray-50/20 group-hover:bg-blue-50/40 tabular-nums"
								>
									{{ index + 1 }}
								</td>
								<td class="px-2 py-2">
									<div class="font-bold text-gray-800 text-xs">
										{{ r.item_name }}
									</div>
									<div
										class="text-[9px] text-gray-400 font-medium tracking-tight"
									>
										{{ r.item_code }}
									</div>
								</td>
								<td
									class="px-2 py-2 text-right text-xs font-semibold text-gray-700 tabular-nums"
								>
									{{ r.order_qty.toLocaleString() }}
								</td>
								<td
									class="px-2 py-2 text-right text-xs font-semibold text-emerald-600 tabular-nums"
								>
									{{ r.produced_qty.toLocaleString() }}
								</td>
								<td
									class="px-2 py-2 text-right text-xs font-semibold text-rose-500 tabular-nums"
								>
									{{ r.balance_qty.toLocaleString() }}
								</td>

								<td class="px-2 py-2">
									<ProductionProgress
										:total="r.order_qty"
										:produced="r.produced_qty"
										:progress="r.progress"
									/>
								</td>

								<td class="px-2 py-2">
									<StatusBadge :status="r.status" />
								</td>

								<td class="px-2 py-2">
									<GanttMini
										:bars="
											r.timeline.filter((b) => !b.label.startsWith('Job'))
										"
									/>
								</td>

								<!-- Job Cards Timeline Column -->
								<td class="px-2 py-2">
									<GanttMini
										:bars="r.timeline.filter((b) => b.label.startsWith('Job'))"
									/>
								</td>
							</tr>
						</template>
					</tbody>
				</table>
			</div>
		</div>

		<!-- Charts Section -->
		<div v-if="rows.length" class="hidden sm:block">
			<ProductionCharts :rows="rows" />
		</div>
	</div>
</template>

<script setup>
import { computed, ref, watch } from "vue";
import { api } from "../services/api";

import StatusBadge from "./StatusBadge.vue";
import GanttMini from "./GanttMini.vue";
import ProductionProgress from "./ProductionProgress.vue";
import ProductionCharts from "./ProductionCharts.vue";
import Kpi from "./Kpi.vue";

const props = defineProps({
	filters: { type: Object, required: true },
});

const rows = ref([]);
const loading = ref(false);

async function load() {
	loading.value = true;
	try {
		const res = await api.getProductionControlDashboard(props.filters);
		rows.value = res?.data?.message.data || [];
	} finally {
		loading.value = false;
	}
}

watch(
	() => props.filters,
	() => {
		load();
	},
	{ deep: true, immediate: true },
);

const totalQty = computed(() => rows.value.reduce((a, r) => a + r.order_qty, 0));

const totalProduced = computed(() => rows.value.reduce((a, r) => a + r.produced_qty, 0));

const avgProgress = computed(() =>
	rows.value.length
		? Math.round(rows.value.reduce((a, r) => a + r.progress, 0) / rows.value.length)
		: 0,
);

const refresh = async () => {
	rows.value = [];
	await load();
};
</script>
