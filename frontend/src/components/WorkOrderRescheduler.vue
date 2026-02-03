<template>
	<div class="p-3 space-y-3">
		<div class="p-4 transition-all duration-300 hover:shadow-md rounded">
			<div
				class="flex flex-wrap items-center gap-4 justify-between rounded-1xl relative z-20"
			>
				<!-- Search Controls -->
				<div class="flex flex-wrap items-center gap-4 flex-grow">
					<div class="flex items-end gap-1">
						<div class="w-56">
							<SearchSelect
								label="Customer"
								doctype="Customer"
								v-model="filters.customer"
								class="transition-all duration-200 group-hover:scale-[1.02]"
							/>
						</div>
						<button
							v-if="filters.customer"
							@click="filters.customer = ''"
							class="h-9 flex items-center justify-center text-xl text-gray-400 hover:text-gray-600 transition-colors"
						>
							X
						</button>
					</div>

					<div class="flex items-end gap-1">
						<div class="w-56">
							<SearchSelect
								label="Sales Order"
								doctype="Sales Order"
								v-model="filters.sales_order"
								class="transition-all duration-200 group-hover:scale-[1.02]"
							/>
						</div>
						<button
							v-if="filters.sales_order"
							@click="filters.sales_order = ''"
							class="h-9 flex items-center justify-center text-xl text-gray-400 hover:text-gray-600 transition-colors"
						>
							X
						</button>
					</div>

					<div class="flex items-end gap-1">
						<div class="w-56">
							<SearchSelect
								label="Mould"
								doctype="Mould"
								v-model="filters.mould"
								class="transition-all duration-200 group-hover:scale-[1.02]"
							/>
						</div>
						<button
							v-if="filters.mould"
							@click="filters.mould = ''"
							class="h-9 flex items-center justify-center text-xl text-gray-400 hover:text-gray-600 transition-colors"
						>
							X
						</button>
					</div>

					<div class="flex items-end gap-1">
						<div class="w-56">
							<SearchSelect
								label="Item"
								doctype="Item"
								v-model="filters.item"
								class="transition-all duration-200 group-hover:scale-[1.02]"
							/>
						</div>
						<button
							v-if="filters.item"
							@click="filters.item = ''"
							class="h-9 flex items-center justify-center text-xl text-gray-400 hover:text-gray-600 transition-colors"
						>
							X
						</button>
					</div>

					<div class="flex items-end gap-1">
						<div class="w-56">
							<SearchSelect
								label="Shift"
								doctype="Shift Type"
								v-model="filters.shift"
								class="transition-all duration-200 group-hover:scale-[1.02]"
							/>
						</div>
						<button
							v-if="filters.shift"
							@click="filters.shift = ''"
							class="h-9 flex items-center justify-center text-xl text-gray-400 hover:text-gray-600 transition-colors"
						>
							X
						</button>
					</div>

					<!-- STATUS FILTER -->
					<div class="flex items-end gap-1">
						<div class="flex flex-col w-56">
							<label class="text-[10px] font-bold text-gray-600">Status</label>
							<select
								v-model="filters.status"
								class="h-10 border border-gray-200 rounded-lg text-sm font-medium text-gray-700 bg-gray-50/50 focus:bg-white focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none transition-all px-3"
							>
								<option value="">All Statuses</option>
								<option value="Draft">Draft</option>
								<option value="In Progress">In Progress</option>
								<option value="Completed">Completed</option>
								<option value="Stopped">Stopped</option>
							</select>
						</div>
						<button
							v-if="filters.status"
							@click="filters.status = ''"
							class="h-9 flex items-center justify-center text-xl text-gray-400 hover:text-gray-600 transition-colors"
						>
							X
						</button>
					</div>

					<!-- MONTH PICKER -->
					<div class="flex items-end gap-1">
						<div class="flex flex-col w-56">
							<label class="text-[10px] font-bold text-gray-600">Month</label>
							<input
								type="month"
								v-model="monthPicker"
								class="h-10 border border-gray-200 rounded-lg text-sm font-medium text-gray-700 bg-gray-50/50 focus:bg-white focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none transition-all px-3"
							/>
						</div>
						<button
							v-if="monthPicker"
							@click="monthPicker = ''"
							class="h-9 flex items-center justify-center text-xl text-gray-400 hover:text-gray-600 transition-colors"
						>
							X
						</button>
					</div>
				</div>

				<!-- Actions -->
				<div class="flex items-center gap-3">
					<button
						@click="resetFilters"
						class="flex items-center gap-2 px-4 py-2 text-sm font-black bg-gray-200 border border-gray-200 rounded hover:border-gray-300 hover:bg-blue-600 hover:text-white transition-all duration-300 active:scale-95 shadow-[0_2px_10px_-3px_rgba(0,0,0,0.07)] hover:shadow-[0_4px_15px_-3px_rgba(0,0,0,0.1)] group"
					>
						<span
							class="text-base transition-transform duration-500 group-hover:rotate-180"
							>↺</span
						>
						Reset Filters
					</button>
				</div>
			</div>
		</div>

		<!-- CALENDAR -->
		<div class="border rounded-sm bg-white p-2 relative text-black">
			<FullCalendar ref="calendarRef" :options="calendarOptions" class="text-black" />

			<!-- HOVER CARD (Compact & Clean) -->
			<div
				v-if="hoveredEvent"
				class="event-tooltip fixed bg-white border border-gray-200 shadow-2xl rounded-2xl p-3 w-72 text-sm z-[9999] transition-all duration-200"
				:style="{ top: hoverPosition.y + 'px', left: hoverPosition.x + 'px' }"
				@mouseenter="keepTooltipOpen"
				@mouseleave="hideTooltip"
			>
				<!-- Header -->
				<div class="flex items-start justify-between mb-2 border-b border-gray-50 pb-2">
					<div class="flex flex-col gap-0.5">
						<span class="text-[8px] font-black text-blue-600 uppercase"
							>Work Order</span
						>
						<a
							:href="'/app/work-order/' + hoveredEvent.wo_name"
							target="_blank"
							class="text-sm font-black text-gray-900 hover:text-blue-700 transition-colors leading-tight"
						>
							{{ hoveredEvent.wo_name }}
						</a>
					</div>
					<div
						:class="[
							'px-1.5 py-0.5 rounded-full text-[8px] font-black uppercase tracking-wider shadow-sm border',
							getStatusColor(hoveredEvent.status).badge,
						]"
					>
						{{ hoveredEvent.status }}
					</div>
				</div>

				<!-- Info Grid -->
				<div class="space-y-2.5">
					<div class="flex gap-2">
						<div
							class="w-7 h-7 rounded-lg bg-blue-50 flex items-center justify-center text-xs shrink-0"
						>
							📦
						</div>
						<div>
							<div
								class="text-[8px] font-bold text-gray-400 uppercase tracking-tight mb-0.5"
							>
								Production Item
							</div>
							<div class="text-[11px] font-bold text-gray-800 leading-tight">
								{{ hoveredEvent.production_item }}
							</div>
						</div>
					</div>

					<div class="grid grid-cols-2 gap-3 pl-9">
						<div>
							<div
								class="text-[8px] font-bold text-gray-400 uppercase tracking-tight mb-0.5"
							>
								Qty
							</div>
							<div class="text-[12px] font-black text-gray-800">
								{{ hoveredEvent.qty || "-" }}
							</div>
						</div>
						<div>
							<div
								class="text-[8px] font-bold text-gray-400 uppercase tracking-tight mb-0.5"
							>
								Mould
							</div>
							<div class="text-[12px] font-black text-gray-800">
								{{ hoveredEvent.mould || "-" }}
							</div>
						</div>
					</div>

					<!-- Timeline Section -->
					<div class="bg-gray-50/80 rounded-xl p-2 border border-gray-100/50">
						<div class="flex items-center gap-1.5 mb-1.5">
							<span class="text-[10px]">🕒</span>
							<span class="text-[8px] font-black text-gray-400 uppercase"
								>Timeline</span
							>
						</div>
						<div class="space-y-1 font-mono text-[10px]">
							<div class="flex justify-between items-center text-gray-500">
								<span>START</span>
								<span class="font-bold text-gray-700">{{
									fmtFull(hoveredEvent.planned_start_date)
								}}</span>
							</div>
							<div class="flex justify-between items-center text-gray-500">
								<span>FINISH</span>
								<span class="font-bold text-gray-700">{{
									fmtFull(hoveredEvent.planned_end_date)
								}}</span>
							</div>
						</div>
					</div>
				</div>

				<!-- Subtle Shadow Pointer -->
				<div
					class="absolute -left-1 top-6 w-3 h-3 bg-white rotate-45 border-l border-b border-gray-200 -z-10 shadow-sm"
				></div>
			</div>
		</div>
	</div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from "vue";
import FullCalendar from "@fullcalendar/vue3";
import dayGridPlugin from "@fullcalendar/daygrid";
import timeGridPlugin from "@fullcalendar/timegrid";
import interactionPlugin from "@fullcalendar/interaction";
import SearchSelect from "./ui/SearchSelect.vue";
import { mssApi } from "../services/rescheduleApi";
import { extractFrappeError } from "../utils/frappe";

/* ---------------- STATE ---------------- */
const calendarRef = ref(null);
const schedule = ref([]);
const holidays = ref([]);

const filters = reactive({
	customer: "",
	sales_order: "",
	mould: "",
	item: "",
	shift: "",
	status: "",
});

const hoveredEvent = ref(null);
const hoverPosition = reactive({ x: 0, y: 0 });
let hoverTimeout = null;

/* ---------------- MONTH PICKER ---------------- */
const today = new Date();
const monthPicker = ref(`${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}`);

/* ---------------- CALENDAR RANGE (SOURCE OF TRUTH) ---------------- */
const visibleRange = reactive({
	from: null,
	to: null,
});

/* ---------------- API PAYLOAD ---------------- */
const apiPayload = computed(() => ({
	from_date: visibleRange.from,
	to_date: visibleRange.to,
	...filters,
}));

/* ---------------- EVENTS ---------------- */
function buildEvents() {
	const woEvents = schedule.value.map((wo) => ({
		id: wo.wo_name,
		title: wo.wo_name,
		start: wo.planned_start_date,
		end: wo.planned_end_date,
		allDay: false,
		editable: wo.status === "Draft",
		extendedProps: wo,
	}));

	const holidayEvents = holidays.value.map((h) => ({
		title: h.description,
		start: h.holiday_date,
		allDay: true,
		display: "background",
		color: "#ff9f89", // Light red for holidays
	}));

	return [...woEvents, ...holidayEvents];
}

/* ---------------- DATE FORMATTER ---------------- */
function toLocalString(date) {
	const y = date.getFullYear();
	const m = String(date.getMonth() + 1).padStart(2, "0");
	const d = String(date.getDate()).padStart(2, "0");
	const h = String(date.getHours()).padStart(2, "0");
	const min = String(date.getMinutes()).padStart(2, "0");
	const s = String(date.getSeconds()).padStart(2, "0");
	// Return YYYY-MM-DD HH:mm:ss (no microseconds)
	return `${y}-${m}-${d} ${h}:${min}:${s}`;
}

function handleEventChange(info) {
	try {
		const { start, end } = info.event;

		// Calculate newEnd if missing, using old duration if available
		let newEnd = end;
		if (!newEnd && info.oldEvent && info.oldEvent.end) {
			const duration = info.oldEvent.end - info.oldEvent.start;
			newEnd = new Date(start.getTime() + duration);
		}
		const safeEnd = newEnd || new Date(start.getTime() + 60 * 60 * 1000); // Fallback 1h

		// Optimistic UI update is already handled by FullCalendar dragging.
		// We just need to persist it.

		mssApi
			.reschedule({
				wo_name: info.event.id,
				planned_start_date: toLocalString(start),
				planned_end_date: toLocalString(safeEnd),
			})
			.then((res) => {
				const responseData = res.data.message;
				if (responseData.success) {
					if (window.frappe) {
						frappe.show_alert({
							message: responseData.message || "Rescheduled successfully",
							indicator: "green",
						});
					}
					// Silent refresh to sync data
					loadSchedule();
				} else {
					info.revert();
					if (window.frappe) {
						frappe.msgprint({
							title: "Reschedule Prevented",
							message: responseData.message || "Validation failed",
							indicator: "orange",
						});
					} else {
						alert(responseData.message || "Reschedule failed");
					}
				}
			})
			.catch((e) => {
				info.revert();
				console.error("Reschedule request failed", e);
				if (window.frappe) {
					frappe.msgprint({
						title: "System Error",
						message: extractFrappeError(e),
						indicator: "red",
					});
				} else {
					alert("Unexpected error: " + e.message);
				}
			});
	} catch (e) {
		info.revert();
		console.error("Reschedule failed locally", e);
	}
}

function handleEventClick(info) {
	// FullCalendar distinguishes click vs drag automatically.
	// eventClick only fires on a click, not after a drag/resize.
	const woName = info.event.id;
	if (woName) {
		const url = `/app/work-order/${woName}`;
		window.open(url, "_blank");
	}
}

function handleEventMouseEnter(info) {
	// Clear any pending hide
	if (hoverTimeout) {
		clearTimeout(hoverTimeout);
		hoverTimeout = null;
	}

	hoveredEvent.value = info.event.extendedProps;

	// Reduced gap so user can easily mouse over it
	// Offset slightly so it doesn't flicker under the cursor immediately
	const x = info.jsEvent.clientX + 5;
	const y = info.jsEvent.clientY + 5;

	hoverPosition.x = x;
	hoverPosition.y = y;
}

function handleEventMouseLeave(info) {
	// Give user time to move to the tooltip
	hoverTimeout = setTimeout(() => {
		hoveredEvent.value = null;
	}, 300); // 300ms delay
}

function keepTooltipOpen() {
	if (hoverTimeout) {
		clearTimeout(hoverTimeout);
		hoverTimeout = null;
	}
}

function hideTooltip() {
	hoveredEvent.value = null;
}

/* ---------------- CALENDAR OPTIONS ---------------- */
const calendarOptions = {
	plugins: [dayGridPlugin, timeGridPlugin, interactionPlugin],
	initialView: "timeGridWeek",
	// timeZone: "UTC", // REMOVED: Using Local view to match user's perspective
	slotDuration: "00:30:00",
	snapDuration: "00:01:00",
	height: "auto",
	editable: true,
	eventResizableFromStart: true,

	// CRITICAL for night shifts:
	// Any event ending after 00:00:00 will be rendered as spanning to that day.
	nextDayThreshold: "00:00:00",

	// Visual style
	eventDisplay: "block",
	displayEventTime: true,

	headerToolbar: {
		left: "prev,next today",
		center: "title",
		right: "dayGridMonth,timeGridWeek",
	},

	events(fetchInfo, successCallback) {
		// We supply events manually via schedule.value watching
		// But FullCalendar needs a function or array.
		// We'll return the buildEvents() result.
		successCallback(buildEvents());
	},

	datesSet(info) {
		visibleRange.from = info.startStr;
		visibleRange.to = new Date(info.end.getTime() - 1).toISOString().slice(0, 10);

		loadSchedule();
	},

	eventDrop: handleEventChange,
	eventMouseEnter: handleEventMouseEnter,
	eventMouseLeave: handleEventMouseLeave,

	slotEventOverlap: true,
	slotMaxTime: "24:00:00",
	slotMinTime: "00:00:00",
	allDaySlot: false,

	eventContent: (arg) => {
		if (arg.event.display === "background" || !arg.event.extendedProps.wo_name) {
			return null;
		}
		return { html: renderWOCard(arg.event.extendedProps) };
	},
};

/* ---------------- WATCHERS ---------------- */
watch(monthPicker, (val) => {
	if (!val) return;
	const parts = val.split("-");
	if (parts.length < 2) return;
	const [y, m] = parts.map(Number);
	calendarRef.value?.getApi().gotoDate(new Date(y, m - 1, 1));
});

// Auto-refresh when filters change
watch(
	filters,
	() => {
		loadSchedule();
	},
	{ deep: true },
);

// Refetch events when schedule changes
watch(schedule, () => {
	calendarRef.value?.getApi().refetchEvents();
});

/* ---------------- API ---------------- */
async function loadSchedule() {
	if (!visibleRange.from || !visibleRange.to) return;

	try {
		const [res, holRes] = await Promise.all([
			mssApi.load(apiPayload.value),
			mssApi.getHolidays(visibleRange.from, visibleRange.to),
		]);

		const scheduleResponse = res.data.message;
		const holidayResponse = holRes.data.message;

		if (scheduleResponse.success) {
			schedule.value = scheduleResponse.data || [];
		} else {
			console.error("Failed to load schedule:", scheduleResponse.message);
		}

		if (holidayResponse.success) {
			holidays.value = holidayResponse.data || [];
		}
	} catch (e) {
		console.error("Failed to load schedule", e);
	}
}

/* ---------------- RESET ---------------- */
function resetFilters() {
	filters.customer = "";
	filters.sales_order = "";
	filters.mould = "";
	filters.item = "";
	filters.shift = "";
	filters.status = "";
	// Watcher will trigger loadSchedule
}

/* ---------------- UI ---------------- */
function getStatusColor(status, isDraft = false) {
	const colors = {
		Draft: {
			border: "border-sky-400",
			bg: "bg-sky-100",
			text: "text-sky-900",
			badge: "bg-sky-600 text-white border-sky-700",
			marker: "bg-sky-500",
			opacity: "opacity-100",
			shadow: "shadow-md shadow-sky-500/20",
		},
		"In Progress": {
			border: "border-green-400",
			bg: "bg-green-100",
			text: "text-green-900",
			badge: "bg-green-600 text-white border-green-700",
			marker: "bg-green-500",
			opacity: "opacity-100",
			shadow: "shadow-md shadow-green-500/20",
		},
		"Not Started": {
			border: "border-orange-400",
			bg: "bg-orange-100",
			text: "text-orange-900",
			badge: "bg-orange-600 text-white border-orange-700",
			marker: "bg-orange-500",
			opacity: "opacity-90",
			shadow: "shadow-sm",
		},
		Submitted: {
			border: "border-orange-400",
			bg: "bg-orange-100",
			text: "text-orange-900",
			badge: "bg-orange-600 text-white border-orange-700",
			marker: "bg-orange-500",
			opacity: "opacity-90",
			shadow: "shadow-sm",
		},
		Completed: {
			border: "border-blue-400",
			bg: "bg-blue-50",
			text: "text-blue-900",
			badge: "bg-blue-600 text-white border-blue-700",
			marker: "bg-blue-600",
			opacity: "opacity-60",
			shadow: "shadow-sm",
		},
		Stopped: {
			border: "border-rose-400",
			bg: "bg-rose-50",
			text: "text-rose-900",
			badge: "bg-rose-600 text-white border-rose-700",
			marker: "bg-rose-600",
			opacity: "opacity-65",
			shadow: "shadow-sm",
		},
		Cancelled: {
			border: "border-slate-400",
			bg: "bg-slate-100",
			text: "text-slate-700",
			badge: "bg-slate-500 text-white border-slate-600",
			marker: "bg-slate-500",
			opacity: "opacity-50",
			shadow: "shadow-sm",
		},
	};
	return (
		colors[status] || {
			border: "border-zinc-400",
			bg: "bg-gradient-to-br from-zinc-50 to-neutral-100",
			text: "text-zinc-900",
			badge: "bg-zinc-500 text-white border-zinc-600",
			marker: "bg-zinc-500",
			opacity: "opacity-70",
			shadow: "shadow-sm",
		}
	);
}

function renderWOCard(wo) {
	const isDraft = wo.status === "Draft";
	const c = getStatusColor(wo.status, isDraft);
	const isProcessing = wo.status === "In Progress";
	const pulseAnimation = isDraft ? "animate-pulse-slow" : isProcessing ? "animate-pulse" : "";
	const borderWidth = isDraft ? "border-[1px]" : "border";
	const draftBadge = isDraft
		? `<div class="absolute -top-1 -right-1 bg-blue-600 text-white text-[7px] font-black px-1.5 py-0.5 rounded-full shadow-lg border border-white">Re SCHEDULING</div>`
		: "";

	return `
    <div class="h-full w-full p-1.5 flex flex-col gap-0.5 overflow-hidden transition-all duration-300 rounded-xl ${borderWidth} ${
		c.border
	} ${c.bg} ${c.text} ${c.shadow} ${c.opacity} hover:opacity-100 cursor-pointer select-none relative ${pulseAnimation}">
      ${draftBadge}
      <!-- Header -->
      <div class="flex items-center gap-1 overflow-hidden min-h-[12px]">
        <span class="w-1.5 h-1.5 rounded-full ${c.marker} flex-shrink-0 ${isProcessing ? "animate-pulse shadow-[0_0_8px_rgba(245,158,11,0.6)]" : isDraft ? "shadow-[0_0_10px_rgba(37,99,235,0.8)]" : ""}"></span>
        <span class="text-[8px] font-black uppercase tracking-tighter truncate opacity-60">${
			wo.wo_name
		}</span>
      </div>

      <!-- Content -->
      <div class="text-[10px] font-black leading-[1.1] line-clamp-2 mt-0.5 px-0.5">
        ${wo.production_item}
      </div>

      <!-- Footer -->
      <div class="mt-auto pt-1 flex items-center justify-between border-t border-black/5 opacity-50 overflow-hidden">
        <div class="flex items-center gap-0.5 min-w-0">
          <span class="text-[8px] opacity-70">⚙️</span>
          <span class="text-[8px] font-bold truncate">${wo.workstation || "-"}</span>
        </div>
        <div class="flex items-center gap-0.5 flex-shrink-0">
          <span class="text-[8px] font-mono font-bold">${fmt(wo.planned_start_date)}</span>
        </div>
      </div>
    </div>
  `;
}

function fmt(dt) {
	if (!dt) return "";
	return new Date(dt).toLocaleTimeString([], {
		hour: "2-digit",
		minute: "2-digit",
		hour12: false,
	});
}

function fmtFull(dt) {
	if (!dt) return "-";
	const d = new Date(dt);
	return (
		d.toLocaleDateString() +
		" " +
		d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", hour12: false })
	);
}

// onMounted removed to prevent double fetch (datesSet triggers initial load)
</script>

<style scoped>
/* FullCalendar Premium Overrides */
:deep(.fc) {
	--fc-border-color: #f8fafc; /* Ultra soft lines */
	--fc-today-bg-color: #f8fbff;
	--fc-highlight-color: rgba(59, 130, 246, 0.04);
	--fc-now-indicator-color: #3b82f6;
	font-family:
		"Inter",
		system-ui,
		-apple-system,
		sans-serif;
	border: none !important;
}

/* Scrollbar Polish */
:deep(.fc-scroller) {
	scrollbar-width: thin;
	scrollbar-color: #e2e8f0 transparent;
}

:deep(.fc-scroller::-webkit-scrollbar) {
	width: 6px;
	height: 6px;
}

:deep(.fc-scroller::-webkit-scrollbar-thumb) {
	background: #e2e8f0;
	border-radius: 10px;
}

:deep(.fc-scroller::-webkit-scrollbar-track) {
	background: transparent;
}

:deep(.fc-header-toolbar) {
	padding: 1.5rem 2rem !important;
	margin-bottom: 0 !important;
	background: #fff;
	border-bottom: 1px solid #f1f5f9;
}

:deep(.fc-toolbar-title) {
	font-size: 1.125rem !important;
	font-weight: 900 !important;
	color: #0f172a;
	letter-spacing: -0.03em;
}

:deep(.fc-button) {
	background: #fff !important;
	border: 1px solid #e2e8f0 !important;
	color: #64748b !important;
	font-weight: 800 !important;
	font-size: 0.65rem !important;
	text-transform: uppercase !important;
	letter-spacing: 0.075em !important;
	padding: 0.6rem 1.25rem !important;
	border-radius: 1rem !important;
	transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
	box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.03) !important;
	border-bottom-width: 2px !important;
}

:deep(.fc-button:hover) {
	background: #f8fafc !important;
	color: #0f172a !important;
	border-color: #cbd5e1 !important;
	transform: translateY(-1px);
}

:deep(.fc-button-active) {
	background: #f1f5f9 !important;
	color: #3b82f6 !important;
	border-color: #3b82f6 !important;
	border-bottom-width: 2px !important;
	box-shadow: inset 0 2px 4px 0 rgba(0, 0, 0, 0.05) !important;
}

:deep(.fc-col-header-cell) {
	padding: 1.25rem 0 !important;
	background: #fff;
	border-bottom: 1px solid #f1f5f9 !important;
}

:deep(.fc-col-header-cell-cushion) {
	font-size: 0.65rem !important;
	font-weight: 900 !important;
	text-transform: uppercase;
	letter-spacing: 0.15em;
	color: #94a3b8;
	text-decoration: none !important;
}

:deep(.fc-timegrid-slot-label-cushion) {
	font-size: 0.6rem !important;
	font-weight: 800 !important;
	color: #cbd5e1;
	text-transform: uppercase;
	letter-spacing: 0.05em;
}

/* Now Indicator Glow */
:deep(.fc-now-indicator-line) {
	border-width: 1px !important;
	box-shadow: 0 0 10px rgba(59, 130, 246, 0.4);
}

:deep(.fc-now-indicator-arrow) {
	border-color: #3b82f6 !important;
	border-width: 6px !important;
	margin-top: -6px !important;
}

/* Event Card Luxury */
:deep(.fc-v-event) {
	background: transparent !important;
	border: none !important;
	box-shadow: none !important;
	margin: 0 !important;
	padding: 1px 2px !important;
	overflow: visible !important;
	transition: z-index 0.3s !important;
}

:deep(.fc-event-main) {
	padding: 0 !important;
	background: transparent !important;
	height: 100%;
}

:deep(.fc-timegrid-event-harness) {
	margin: 0 !important;
}

/* Tooltip Animation */
.event-tooltip {
	z-index: 9999;
	animation: tooltipFadeIn 0.25s cubic-bezier(0.16, 1, 0.3, 1);
	transform-origin: left center;
}

@keyframes tooltipFadeIn {
	from {
		opacity: 0;
		transform: scale(0.95) translateX(-10px);
	}
	to {
		opacity: 1;
		transform: scale(1) translateX(0);
	}
}

div {
	color: inherit;
}

/* Custom slow pulse animation for draft work orders */
@keyframes pulse-slow {
	0%,
	100% {
		opacity: 1;
		transform: scale(1);
	}
	50% {
		opacity: 0.95;
		transform: scale(1.01);
	}
}

.animate-pulse-slow {
	animation: pulse-slow 3s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}
</style>
