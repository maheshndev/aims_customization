<template>
	<div class="p-4 bg-white rounded shadow space-y-4">
		<p class="text-xs text-gray-500">
			Capacity Planner for calculate machine capacity and plan work orders
		</p>
		<div class="flex flex-wrap items-center justify-between gap-4">
			<div class="flex gap-2">
				<button
					class="px-3 py-1 rounded bg-blue-100 hover:bg-blue-200"
					@click="openModal('validate')"
					:disabled="!selectedRows.length || hasValidationErrors"
				>
					Validate Capacity
				</button>

				<button
					class="px-3 py-1 rounded bg-green-200 hover:bg-green-300"
					@click="openModal('create')"
					:disabled="!selectedRows.length || hasValidationErrors"
				>
					+ Plan & Create WOs
				</button>
			</div>
		</div>

		<!-- Scheduling Modal -->
		<div
			v-if="showModal"
			class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[100] p-4 md:p-6"
		>
			<div
				class="bg-gray-50 rounded-xl shadow-2xl max-w-7xl w-full max-h-[96vh] flex flex-col overflow-hidden relative border-2 border-blue-100"
			>
				<!-- Header -->
				<div class="bg-white p-4 py-3 border-b shrink-0">
					<div class="flex items-center justify-between">
						<div>
							<h3 class="font-bold text-xl text-blue-800 flex items-center gap-2">
								<svg
									xmlns="http://www.w3.org/2000/svg"
									class="h-6 w-6 text-blue-600"
									fill="none"
									viewBox="0 0 24 24"
									stroke="currentColor"
								>
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										stroke-width="2"
										d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01"
									/>
								</svg>
								Production Planning Dashboard
							</h3>
							<p class="text-[11px] text-gray-500 mt-0.5">
								Verify machine availability, select production time slots, and
								adjust materials.
							</p>
						</div>
						<button
							@click="closeModal"
							class="text-gray-400 hover:text-gray-600 transition-colors"
						>
							<svg
								xmlns="http://www.w3.org/2000/svg"
								class="h-5 w-5"
								fill="none"
								viewBox="0 0 24 24"
								stroke="currentColor"
							>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M6 18L18 6M6 6l12 12"
								/>
							</svg>
						</button>
					</div>
				</div>

				<!-- Main Content Container -->
				<div
					class="flex-1 overflow-y-auto p-2 py-2 space-y-2 scrollbar-thin scrollbar-thumb-blue-200 bg-white"
				>
					<!-- Production Period Controls -->
					<div
						class="bg-blue-50/10 p-2 rounded-lg border border-blue-100 shadow-sm space-y-2"
					>
						<!-- Row 1: Utilization, From Date, From Time (3 cols) -->
						<div class="grid grid-cols-3 md:grid-cols-3 gap-2">
							<div class="flex flex-col">
								<label class="text-[9px] font-bold text-blue-900 uppercase mb-0.5"
									>Utilization %</label
								>
								<input
									type="number"
									v-model.number="utilization"
									min="1"
									max="100"
									class="border rounded-md px-2 py-1 w-full focus:ring-1 focus:ring-blue-400 focus:outline-none shadow-sm font-semibold text-xs"
								/>
							</div>
							<div class="flex flex-col">
								<label class="text-[9px] font-bold text-blue-900 uppercase mb-0.5"
									>From Date</label
								>
								<input
									type="date"
									v-model="planStartWrapper"
									@click="
										$event.target.showPicker
											? $event.target.showPicker()
											: null
									"
									class="border rounded-md px-2 py-1 w-full focus:ring-1 focus:ring-blue-400 focus:outline-none shadow-sm font-semibold text-xs cursor-pointer"
								/>
							</div>
							<div class="flex flex-col">
								<label class="text-[9px] font-bold text-blue-900 uppercase mb-0.5"
									>From Time</label
								>
								<input
									type="time"
									v-model="planStartTime"
									@click="
										$event.target.showPicker
											? $event.target.showPicker()
											: null
									"
									@focus="
										$event.target.showPicker
											? $event.target.showPicker()
											: null
									"
									class="border rounded-md px-2 py-1 w-full focus:ring-1 focus:ring-blue-400 focus:outline-none shadow-sm font-semibold text-xs cursor-pointer"
								/>
							</div>
						</div>

						<!-- Row 2: To Date, To Time (Next row) -->
						<div class="grid grid-cols-3 md:grid-cols-3 gap-2">
							<div class="flex flex-col">
								<label class="text-[9px] font-bold text-blue-900 uppercase mb-0.5"
									>To Date</label
								>
								<input
									type="date"
									v-model="planEnd"
									@click="
										$event.target.showPicker
											? $event.target.showPicker()
											: null
									"
									class="border rounded-md px-2 py-1 w-full focus:ring-1 focus:ring-blue-400 focus:outline-none shadow-sm font-semibold text-xs cursor-pointer"
								/>
							</div>
							<div class="flex flex-col">
								<label class="text-[9px] font-bold text-blue-900 uppercase mb-0.5"
									>To Time</label
								>
								<input
									type="time"
									v-model="planEndTime"
									@click="
										$event.target.showPicker
											? $event.target.showPicker()
											: null
									"
									@focus="
										$event.target.showPicker
											? $event.target.showPicker()
											: null
									"
									class="border rounded-md px-2 py-1 w-full focus:ring-1 focus:ring-blue-400 focus:outline-none shadow-sm font-semibold text-xs cursor-pointer"
								/>
							</div>
							<!-- Third col empty for layout -->
							<div class="hidden md:block"></div>
						</div>

						<!-- Row 3: Buttons (Next row) -->
						<div class="flex gap-2 pt-1.5 border-t border-blue-100/30">
							<button
								class="px-2 py-1 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-bold shadow transition-all active:scale-95 flex items-center gap-2 text-[11px]"
								@click="checkAvailability"
							>
								<svg
									xmlns="http://www.w3.org/2000/svg"
									class="h-3 w-3"
									viewBox="0 0 20 20"
									fill="currentColor"
								>
									<path
										fill-rule="evenodd"
										d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
										clip-rule="evenodd"
									/>
								</svg>
								Check Availability
							</button>
							<button
								class="px-3 py-1 bg-white text-gray-500 border border-gray-200 rounded-lg hover:bg-gray-50 transition-all font-bold text-[11px] shadow-sm"
								@click="resetFields"
							>
								Reset
							</button>
							<button
								v-if="
									modalAction === 'create' && Object.keys(availableSlots).length
								"
								class="px-3 py-1 bg-orange-50 text-orange-700 border border-orange-200 rounded-lg hover:bg-orange-100 font-bold transition-all shadow-sm text-[11px]"
								@click="toggleMaterials"
							>
								Adjust RMs
							</button>
						</div>
					</div>

					<!-- Main Scrollable Section for Slots and Materials -->
					<div class="max-h-[60vh] overflow-y-auto pr-2 space-y-2">
						<!-- Available Slots Selection -->
						<div v-if="Object.keys(availableSlots).length" class="mt-2 border-t pt-2">
							<h4 class="font-bold text-sm mb-2 text-gray-700">
								Available Time Slots (Select multiple for splitting)
							</h4>
							<div class="space-y-4">
								<div
									v-for="(slots, key) in availableSlots"
									:key="key"
									class="bg-gray-50 p-2 rounded border"
								>
									<div
										class="text-xs font-semibold text-gray-600 mb-1 flex justify-between"
									>
										<span>{{ getRowDesc(key) }}</span>
										<span class="text-blue-600"
											>Selected Qty: {{ getSelectedQty(key) }} /
											{{ getRequiredQty(key) }}</span
										>
									</div>
									<div class="flex flex-wrap gap-2">
										<div
											v-for="(slot, idx) in slots"
											:key="idx"
											class="px-3 py-2 text-xs border rounded bg-white hover:bg-blue-50 cursor-pointer transition-colors text-left shadow-sm min-w-[200px] flex items-center justify-between"
											:class="{
												'border-blue-500 bg-blue-50 ring-1 ring-blue-500':
													isSlotSelected(key, slot),
											}"
											@click="toggleSlot(key, slot)"
										>
											<div>
												<div class="font-medium text-blue-700">
													{{ slot.desc }}
												</div>
												<div class="text-gray-500 mt-1">
													Avail: {{ slot.duration_hrs }}h | Max Qty:
													{{ slot.max_qty }}
												</div>
											</div>
											<input
												type="checkbox"
												:checked="isSlotSelected(key, slot)"
												class="rounded text-blue-600 ml-2"
											/>
										</div>
										<div
											v-if="!slots.length"
											class="text-xs text-red-500 italic"
										>
											No valid schedule found in this period.
										</div>
									</div>
								</div>
							</div>
						</div>

						<!-- Raw Materials Adjustment (Visible on click) -->
						<div
							v-if="showMaterials"
							class="mt-4 border-t-4 border-orange-400 pt-6 animate-fade-in bg-white p-4 md:p-6 rounded-2xl shadow-xl space-y-4"
						>
							<div class="flex items-center justify-between">
								<h4
									class="font-black text-xl text-orange-900 flex items-center gap-3"
								>
									<span class="bg-orange-100 p-2 rounded-lg text-orange-600">
										<svg
											xmlns="http://www.w3.org/2000/svg"
											class="h-6 w-6"
											fill="none"
											viewBox="0 0 24 24"
											stroke="currentColor"
										>
											<path
												stroke-linecap="round"
												stroke-linejoin="round"
												stroke-width="2"
												d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
											/>
										</svg>
									</span>
									Raw Material BOM Overrides
								</h4>
								<div
									class="text-[10px] text-orange-400 bg-orange-50 px-3 py-1 rounded-full font-bold uppercase tracking-widest border border-orange-100"
								>
									Live Recalculation Enabled
								</div>
							</div>

							<div
								class="overflow-x-auto border-2 border-gray-50 rounded-2xl shadow-inner scrollbar-thin"
							>
								<table class="min-w-full text-xs">
									<thead
										class="bg-gray-900 text-white uppercase text-[10px] tracking-widest font-black sticky top-0 z-10"
									>
										<tr>
											<th
												class="px-2 py-2 text-left border-r border-gray-800"
											>
												Sales Order ID
											</th>
											<th
												class="px-2 py-2 text-left border-r border-gray-800"
											>
												Production Item
											</th>
											<th
												class="px-2 py-2 text-left border-r border-gray-800"
											>
												Material Name
											</th>
											<th
												class="px-2 py-2 text-center border-r border-gray-800"
											>
												UOM
											</th>
											<th
												class="px-2 py-2 text-right border-r border-gray-800 bg-orange-900/40"
											>
												Required Total
											</th>
											<th
												class="px-2 py-2 text-right border-r border-gray-800"
											>
												Standard %
											</th>
											<th class="px-2 py-2 text-right w-48 bg-orange-600/20">
												Adjust Qty %
											</th>
										</tr>
									</thead>
									<tbody class="divide-y divide-gray-100">
										<template v-for="r in selectedRows" :key="r.rowKey">
											<tr
												v-for="(rm, idx) in r.raw_materials"
												:key="idx"
												class="hover:bg-orange-50/50 transition-all duration-200 group"
											>
												<td
													class="px-2 py-2 text-gray-500 font-mono text-[10px] border-r border-gray-50"
												>
													{{ r.sales_order }}
												</td>
												<td class="px-2 py-2 border-r border-gray-50">
													<div
														class="font-bold text-blue-900 text-[11px]"
													>
														{{ r.item_code }}
													</div>
													<div class="text-[9px] text-gray-400 italic">
														Target Qty: {{ r.schedule_qty }}
													</div>
												</td>
												<td class="px-2 py-2 border-r border-gray-50">
													<div
														class="font-bold text-gray-800 text-[11px] group-hover:text-orange-900 transition-colors"
													>
														{{ rm.item_name }}
													</div>
													<div
														class="text-[9px] text-gray-400 font-mono"
													>
														{{ rm.item_code }}
													</div>
												</td>
												<td
													class="px-2 py-2 text-center border-r border-gray-50"
												>
													<span
														class="bg-gray-100 text-gray-600 px-2 py-1 rounded-md text-[10px] font-black uppercase ring-1 ring-gray-200"
													>
														{{ rm.uom }}
													</span>
												</td>
												<td
													class="px-2 py-2 text-right font-black text-lg text-blue-700 bg-blue-50/20 border-r border-gray-50"
												>
													{{ rm.total_adjusted_qty }}
												</td>
												<td
													class="px-2 py-2 text-right text-gray-400 border-r border-gray-50 font-medium"
												>
													{{ rm.base_rm_percentage }}%
												</td>
												<td class="px-2 py-2 text-right bg-orange-50/30">
													<div
														class="flex items-center justify-end gap-2"
													>
														<input
															type="number"
															v-model.number="
																rm.adjustable_rm_percentage
															"
															step="0.01"
															@input="recalculateMaterial(rm)"
															class="border-2 border-orange-200 rounded-xl px-3 py-2 w-28 text-right text-orange-800 font-black text-base focus:border-orange-500 focus:ring-4 focus:ring-orange-100 focus:outline-none transition-all shadow-sm"
														/>
														<span
															class="text-sm text-orange-500 font-black"
															>%</span
														>
													</div>
												</td>
											</tr>
										</template>
										<tr
											v-if="
												!selectedRows.length ||
												!selectedRows.some((r) => r.raw_materials.length)
											"
											class="text-center py-20"
										>
											<td
												colspan="7"
												class="py-20 text-gray-300 italic font-medium"
											>
												No materials found for selected order lines. Please
												ensure BOMs are loaded.
											</td>
										</tr>
									</tbody>
								</table>
							</div>
						</div>
					</div>

					<!-- Availability Preview Table (Legacy/fallback) -->
					<div
						v-if="schedulePreview.length"
						class="mt-4 border rounded overflow-hidden max-h-40 overflow-y-auto"
					>
						<table class="min-w-full text-xs text-left">
							<thead class="bg-gray-50 font-medium text-gray-700 sticky top-0">
								<tr>
									<th class="px-2 py-2">Item</th>
									<th class="px-2 py-2">Machine</th>
									<th class="px-2 py-2">Mould</th>
									<th class="px-2 py-2">Available From</th>
									<th class="px-2 py-2">Status</th>
								</tr>
							</thead>
							<tbody class="divide-y divide-gray-100">
								<tr
									v-for="row in schedulePreview"
									:key="row.row_key"
									:class="{
										'bg-green-50': row.is_available,
										'bg-yellow-50': !row.is_available,
									}"
								>
									<td class="px-2 py-2">{{ row.item_code }}</td>
									<td class="px-2 py-2">{{ row.machine }}</td>
									<td class="px-2 py-2">{{ row.mould || "-" }}</td>
									<td class="px-2 py-2 font-mono text-blue-600">
										{{
											row.available_start &&
											row.available_start.split(" ")[0]
										}}
										<span class="text-gray-500">{{
											row.available_start &&
											row.available_start.split(" ")[1]
										}}</span>
									</td>
									<td
										class="px-2 py-2"
										:class="{
											'text-green-600 font-medium': row.is_available,
											'text-orange-600': !row.is_available,
										}"
									>
										{{ row.reason }}
									</td>
								</tr>
							</tbody>
						</table>
					</div>
				</div>

				<!-- Sticky Footer -->
				<div class="bg-white p-2 border-t shrink-0 flex justify-end gap-3 shadow-inner">
					<button
						@click="closeModal"
						class="px-3 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 font-bold rounded-lg transition-all"
					>
						Cancel
					</button>
					<button
						@click="confirmAction"
						class="px-3 py-2 bg-blue-600 text-white hover:bg-blue-700 font-bold rounded-lg shadow-md transition-all active:scale-95"
					>
						Proceed & Create
					</button>
				</div>
			</div>
		</div>

		<div v-if="!rows.length" class="text-gray-400 text-sm">No items selected</div>

		<div v-else class="overflow-auto">
			<table class="min-w-[1500px] w-full border text-sm">
				<thead class="bg-gray-100 text-xs uppercase sticky top-0 z-10 shadow-sm">
					<tr>
						<th class="border p-2 text-center bg-gray-100">
							<input type="checkbox" v-model="selectAll" @change="toggleAll" />
						</th>
						<th class="border p-2 bg-gray-100">#</th>
						<th class="border p-2 whitespace-nowrap bg-gray-100">Customer Name</th>
						<th class="border p-2 whitespace-nowrap bg-gray-100">Sales Order ID</th>
						<th class="border p-2 whitespace-nowrap bg-gray-100">SO Item Code</th>
						<th class="border p-2 whitespace-nowrap bg-gray-100">Delivery Date</th>
						<th class="border p-2 whitespace-nowrap bg-gray-100">BOM ID</th>

						<th class="border p-2 whitespace-nowrap bg-gray-100">Machine Name</th>
						<th class="border p-2 whitespace-nowrap bg-gray-100">Mould ID</th>
						<th class="border p-2 whitespace-nowrap text-right bg-gray-100">
							Total Qty
						</th>
						<th class="border p-2 whitespace-nowrap text-right bg-gray-100">
							Planned
						</th>
						<th class="border p-2 whitespace-nowrap text-right bg-blue-50">To Plan</th>
						<th class="border p-2 whitespace-nowrap text-right bg-gray-100">Cycle</th>
						<th class="border p-2 whitespace-nowrap text-right bg-gray-100">Cavity</th>
						<th class="border p-2 whitespace-nowrap text-right bg-gray-100">Pcs/Hr</th>
						<th class="border p-2 whitespace-nowrap text-right bg-gray-100">
							Req Hrs
						</th>
						<th class="border p-2 whitespace-nowrap text-right bg-gray-100">
							Avail Hrs In Period
						</th>
						<th class="border p-2 whitespace-nowrap text-right bg-gray-100">
							Gap in Hrs
						</th>
						<th class="border p-2 whitespace-nowrap bg-gray-100">Status</th>
						<th class="border p-2 whitespace-nowrap bg-gray-100">RM Status</th>
						<th class="border p-2 whitespace-nowrap text-center bg-gray-100">
							Preview
						</th>
					</tr>
				</thead>

				<tbody>
					<template v-for="(r, i) in rows" :key="r.rowKey">
						<tr
							class="hover:bg-gray-50"
							:class="{
								'bg-red-50': r.validation_error,
								'bg-green-50': !r.validation_error && r.required_hours,
							}"
						>
							<td class="border p-2 text-center">
								<input type="checkbox" :value="r.rowKey" v-model="selectedKeys" />
							</td>
							<td class="border p-2 whitespace-nowrap">{{ i + 1 }}</td>
							<td class="border p-2 whitespace-nowrap font-medium">
								{{ r.customer }}
							</td>
							<td class="border p-2 whitespace-nowrap">{{ r.sales_order }}</td>
							<td class="border p-2 whitespace-nowrap relative group cursor-pointer">
								<div
									:style="{ paddingLeft: r.level * 20 + 'px' }"
									class="flex items-center gap-1"
								>
									<span
										v-if="r.level > 0"
										class="text-xs bg-gray-100 text-gray-500 px-1 rounded"
										>L{{ r.level }}</span
									>
									<span>{{ r.item_code }}</span>
								</div>
								<!-- Tooltip -->
								<div
									class="absolute left-1/2 transform -translate-x-1/2 -top-8 bg-gray-800 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap"
								>
									{{ r.item_name }}
								</div>
							</td>
							<td class="border p-2 whitespace-nowrap">
								{{
									r.delivery_date
										? new Date(r.delivery_date).toLocaleDateString()
										: "—"
								}}
							</td>

							<td class="border p-2 whitespace-nowrap">{{ r.bom_no }}</td>
							<td class="border p-2 whitespace-nowrap">{{ r.machine }}</td>
							<td class="border p-2 whitespace-nowrap relative group cursor-pointer">
								{{ r.mould || "—" }}
								<!-- Tooltip -->
								<div
									class="absolute left-1/2 transform -translate-x-1/2 -top-8 bg-gray-800 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap"
								>
									{{ r.mould_name }}
								</div>
							</td>
							<td class="border p-2 whitespace-nowrap text-right text-gray-500">
								{{ r.total_so_qty }}
							</td>
							<td
								class="border p-2 whitespace-nowrap text-right text-orange-600 font-medium"
							>
								{{ r.planned_qty }}
							</td>
							<td
								class="border p-2 whitespace-nowrap text-right font-bold bg-blue-50/30"
							>
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

							<td class="border p-2 whitespace-nowrap text-center">
								<span
									class="px-2 py-0.5 rounded-full text-xs font-medium"
									:class="
										r.rm_sufficient
											? 'bg-green-100 text-green-800'
											: 'bg-red-100 text-red-800'
									"
								>
									{{ r.rm_sufficient ? "Sufficient" : "Shortage" }}
								</span>
							</td>

							<td class="border p-2 text-center whitespace-nowrap">
								<button
									class="px-2 py-0.5 text-xs border rounded bg-gray-50"
									@click="togglePreview(r)"
								>
									{{ preview[r.rowKey] ? "Hide" : "View" }}
								</button>
							</td>
						</tr>

						<tr v-if="preview[r.rowKey]">
							<td colspan="15" class="bg-gray-50 p-3 whitespace-nowrap">
								<div class="flex flex-wrap gap-2">
									<div
										v-for="(p, idx) in preview[r.rowKey]"
										:key="idx"
										class="px-2 py-1 border rounded text-xs bg-white"
									>
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
import { extractFrappeError, showMessage } from "../utils/frappe";

const props = defineProps({
	capBoms: { type: Array, default: () => [] },
	rawMaterials: { type: Array, default: () => [] },
});

const emit = defineEmits(["refresh", "message"]);

const rows = ref([]);
const preview = ref({});
const selectedKeys = ref([]);
const selectAll = ref(false);
const utilization = ref(90);
// planStart: Date string YYYY-MM-DD
const planStart = ref(today());
// planStartTime: Time string HH:mm
const planStartTime = ref("07:30");
const planEnd = ref(null);
const planEndTime = ref("22:00");

const showModal = ref(false);
const modalAction = ref(null);
const schedulePreview = ref([]);
const availableSlots = ref({});
const selectedSlotsMap = ref({}); // { rowKey: [{start, end, qty}] }
const showMaterials = ref(false);

const planStartWrapper = computed({
	get: () => planStart.value,
	set: (val) => {
		planStart.value = val;
	},
});

const modalTitle = computed(() => {
	if (modalAction.value === "validate") return "Validate Capacity";
	if (modalAction.value === "create") return "Plan & Create Work Orders";
	return "Capacity Planning";
});

function openModal(action) {
	modalAction.value = action;
	showModal.value = true;
	schedulePreview.value = []; // Reset on open
	// Store current values for reset if needed
	initialValues.value = {
		utilization: utilization.value,
		planStart: planStart.value,
		planStartTime: planStartTime.value,
		planEnd: planEnd.value,
		planEndTime: planEndTime.value,
	};
}

const initialValues = ref({});

function resetFields() {
	if (initialValues.value.utilization !== undefined) {
		utilization.value = initialValues.value.utilization;
		planStart.value = initialValues.value.planStart;
		planStartTime.value = initialValues.value.planStartTime;
		planEnd.value = initialValues.value.planEnd;
		planEndTime.value = initialValues.value.planEndTime;
	} else {
		// Fallback to hardcoded defaults
		utilization.value = 90;
		planStart.value = today();
		planStartTime.value = "07:30";
		planEnd.value = null;
		planEndTime.value = "22:00";
	}

	schedulePreview.value = [];
	availableSlots.value = {};
	selectedSlotsMap.value = {};

	showMessage({
		title: "Reset",
		message: "Fields restored to initial state.",
		indicator: "blue",
	});
}

function closeModal() {
	showModal.value = false;
	modalAction.value = null;
	schedulePreview.value = []; // Reset on close
	availableSlots.value = {};
	selectedSlotsMap.value = {};
	showMaterials.value = false;
}

function refreshData() {
	// Clear previous results
	schedulePreview.value = [];
	rows.value.forEach((r) => {
		r.validation_error = null;
		r.capacity_gap = null;
		r.available_hours = null;
		r.required_hours = null;
		r.pcs_per_hour = null;
	});
	preview.value = {};

	// Re-trigger validation or check availability if inputs are valid
	if (validateInputs()) {
		if (modalAction.value === "validate") {
			validateCapacity();
		} else {
			checkAvailability();
		}
		showMessage({
			title: "Refreshed",
			message: "Data refreshed based on new inputs.",
			indicator: "green",
		});
	}
}

function confirmAction() {
	if (!validateInputs()) return;

	if (modalAction.value === "validate") validateCapacity();
	else if (modalAction.value === "create") createWorkOrders();
	closeModal();
}

function validateInputs() {
	if (utilization.value <= 0 || utilization.value > 100) {
		showMessage({
			title: "Validation Error",
			message: "Utilization must be between 1 and 100%",
			indicator: "red",
		});
		return false;
	}
	if (!planEnd.value) {
		showMessage({
			title: "Validation Error",
			message: "Plan End Date is required",
			indicator: "red",
		});
		return false;
	}
	if (new Date(planEnd.value) < new Date(planStart.value)) {
		showMessage({
			title: "Validation Error",
			message: "Plan End Date cannot be before Plan Start Date",
			indicator: "red",
		});
		return false;
	}
	return true;
}

async function checkAvailability() {
	if (!selectedRows.value.length) {
		showMessage({
			title: "Validation Error",
			message: "Please select at least one order",
			indicator: "orange",
		});
		return;
	}
	if (!planStart.value) {
		showMessage({
			title: "Validation Error",
			message: "Plan Start Date is required",
			indicator: "orange",
		});
		return;
	}
	try {
		// Fetch Available Slots
		const lines = selectedRows.value.map((r) => ({
			rowKey: r.rowKey,
			item_code: r.item_code,
			machine: r.machine,
			mould: r.mould,
			schedule_qty: r.schedule_qty,
			cycle_time: r.cycle_time,
			cavity: r.cavity,
		}));

		const payload = {
			lines,
			plan_start_date: planStart.value,
			plan_start_time: planStartTime.value, // Pass time too
			plan_end_date: planEnd.value,
			plan_end_time: planEndTime.value,
		};

		const res = await api.getAvailabilitySlots(payload);
		availableSlots.value = res.data.message || {};

		// Also fetch legacy preview if needed, or just rely on slots
		// For simplicity, we assume slots are the primary way now.

		showMessage({
			title: "Availability Checked",
			message: `Found slots for ${Object.keys(availableSlots.value).length} items.`,
			indicator: "green",
		});
	} catch (e) {
		console.error(e);
		const msg = e.message || "Failed to check availability";
		showMessage({ title: "Error", message: msg, indicator: "red" });
	}
}

function getRowDesc(key) {
	const r = rows.value.find((x) => x.rowKey === key);
	return r ? `${r.item_code} @ ${r.machine}` : key;
}

function formatTime(dtStr) {
	if (!dtStr) return "";
	// dtStr is "YYYY-MM-DD HH:mm:ss"
	const [d, t] = dtStr.split(" ");
	// Return "HH:mm (Day)" or just HH:mm if today?
	// Let's keep it simple: "DD-MM HH:mm"
	const [y, m, day] = d.split("-");
	const [h, min] = t.split(":");
	return `${day}-${m} ${h}:${min}`;
}

function applySlot(slot) {
	// Slot: { start: "YYYY-MM-DD HH:mm:ss", end: "..." }
	const [sd, st] = slot.start.split(" ");
	const [ed, et] = slot.end.split(" ");

	planStart.value = sd;
	planStartTime.value = st.slice(0, 5); // HH:mm
	planEnd.value = ed;
	planEndTime.value = et.slice(0, 5);

	showMessage({
		title: "Time Selected",
		message: `Plan updated to selected slot: ${st} - ${et}`,
		indicator: "green",
	});
}

function toggleSlot(rowKey, slot) {
	if (!selectedSlotsMap.value[rowKey]) selectedSlotsMap.value[rowKey] = [];

	const idx = selectedSlotsMap.value[rowKey].findIndex(
		(s) => s.start === slot.start && s.end === slot.end,
	);
	if (idx > -1) {
		selectedSlotsMap.value[rowKey].splice(idx, 1);
	} else {
		// Calculate suggested qty for this slot to fill remaining
		const req = getRequiredQty(rowKey);
		const current = getSelectedQty(rowKey);
		const remaining = Math.max(0, req - current);
		const qty = Math.min(remaining, slot.max_qty || remaining);

		selectedSlotsMap.value[rowKey].push({
			start: slot.start,
			end: slot.end,
			qty: qty,
			desc: slot.desc,
		});
	}
}

function isSlotSelected(rowKey, slot) {
	if (!selectedSlotsMap.value[rowKey]) return false;
	return selectedSlotsMap.value[rowKey].some(
		(s) => s.start === slot.start && s.end === slot.end,
	);
}

function getSelectedQty(rowKey) {
	if (!selectedSlotsMap.value[rowKey]) return 0;
	return selectedSlotsMap.value[rowKey].reduce((a, b) => a + (b.qty || 0), 0);
}

function getRequiredQty(rowKey) {
	const r = rows.value.find((x) => x.rowKey === rowKey);
	return r ? r.schedule_qty : 0;
}

function toggleMaterials() {
	showMaterials.value = !showMaterials.value;
}

function recalculateMaterial(rm) {
	if (rm.adjustable_rm_percentage === null || rm.adjustable_rm_percentage === undefined) return;

	const baseQty = rm.total_base_qty || 0;
	const basePercent = rm.base_rm_percentage || 100;
	const adjPercent = rm.adjustable_rm_percentage;

	// Formula: newQty = (baseQty * adjPercent) / basePercent
	let newQty = (baseQty * adjPercent) / basePercent;

	// Rounding logic for Whole Numbers (Nos, Each)
	const uom = (rm.uom || "").toLowerCase();
	if (uom === "nos" || uom === "each") {
		// User mentioned 21600 * 1.1% = 237.6 -> 238
		// This suggests rounding up or nearest. Math.ceil is usually manufacturing standard for Nos.
		// But let's use Math.round as it matches 237.6 -> 238.
		newQty = Math.round(newQty);
	} else {
		newQty = +newQty.toFixed(4);
	}

	rm.total_adjusted_qty = newQty;
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
		.filter((b) => !b.has_work_order)
		.map((b, i) => {
			// 3. Inject updated Raw Materials (percentages/qtys) filtered for this specific SO + BOM
			const lineRMs = rms
				.filter((r) => r.sales_order === b.sales_order && r.bom_no === b.bom_no)
				.map((r) => ({
					item_code: r.rm_item_code,
					item_name: r.rm_item_name,
					uom: r.stock_uom,
					base_rm_percentage: r.base_rm_percentage,
					adjustable_rm_percentage: r.adjustable_rm_percentage,
					total_adjusted_qty: r.required_qty,
					total_base_qty: r.base_required_qty,
					is_sufficient: r.is_sufficient,
					source_warehouse: r.default_warehouse,
				}));

			const rm_sufficient = lineRMs.every((r) => r.is_sufficient);

			return {
				...b,
				rowKey: `${b.bom_no}_${b.sales_order}_${b.level || 0}_${i}`,
				schedule_qty: Number(b.required_for_selected_qty || 0),

				machine: b.selected_workstation,
				mould: b.selected_mould || null,
				raw_materials: lineRMs,
				rm_sufficient: rm_sufficient,
				validation_error: null,
			};
		});
	preview.value = {};
	selectedKeys.value = [];
}

const selectedRows = computed(() =>
	rows.value.filter((r) => selectedKeys.value.includes(r.rowKey)),
);

const totalRequiredHours = computed(() =>
	selectedRows.value.reduce((a, b) => a + Number(b.required_hours || 0), 0).toFixed(2),
);

function toggleAll() {
	selectedKeys.value = selectAll.value ? rows.value.map((r) => r.rowKey) : [];
}

watch(selectedKeys, (val) => {
	selectAll.value = rows.value.length > 0 && val.length === rows.value.length;

	// Auto-default planStart if at least one row is selected
	if (val.length > 0) {
		const dates = selectedRows.value
			.map((r) => r.delivery_date)
			.filter(Boolean)
			.map((d) => new Date(d));

		if (dates.length > 0) {
			const earliest = new Date(Math.min(...dates));
			const todayDt = new Date();
			todayDt.setHours(0, 0, 0, 0);

			// Use max(the earliest SO date, today)
			const target = earliest < todayDt ? todayDt : earliest;
			const targetStr = target.toISOString().slice(0, 10);
			planStart.value = targetStr;
			planEnd.value = targetStr; // Default End Date to Start Date
		}
	}
});

const hasValidationErrors = computed(() => selectedRows.value.some((r) => r.validation_error));

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
			plan_end_time: planEndTime.value,
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
			plan_end_time: planEndTime.value,
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
				delivery_date: row.delivery_date,
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
			plan_end_time: planEndTime.value,
			lines: selectedRows.value.map((r) => {
				const slots = selectedSlotsMap.value[r.rowKey] || [];

				// Format modified items for this SO
				const modified_items = r.raw_materials.map((rm) => ({
					item_code: rm.item_code,
					qty: rm.total_adjusted_qty,
					source_warehouse: rm.source_warehouse,
				}));

				return {
					item_code: r.item_code,
					schedule_qty: r.schedule_qty,
					cycle_time: r.cycle_time,
					cavity: r.cavity,
					machine: r.machine,
					mould: r.mould || null,
					bom_no: r.bom_no,
					raw_materials: r.raw_materials,
					sales_order: r.sales_order,
					delivery_date: r.delivery_date,
					selected_slots: slots,
					modified_items: showMaterials.value ? modified_items : null,
				};
			}),
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
