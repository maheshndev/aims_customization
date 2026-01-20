<template>
	<div class="p-3 space-y-3">
		<!-- FILTER BAR -->
		<div class="flex flex-wrap items-end gap-3 bg-white p-3 rounded shadow-sm">
			<div class="flex items-end gap-1">
				<SearchSelect
					label="Sales Order"
					doctype="Sales Order"
					v-model="filters.sales_order"
				/>
				<button
					v-if="filters.sales_order"
					@click="filters.sales_order = ''"
					class="text-gray-400 hover:text-red-500 pb-2"
				>
					✕
				</button>
			</div>
			<div class="flex items-end gap-1">
				<SearchSelect label="Mould" doctype="Mould" v-model="filters.mould" />
				<button
					v-if="filters.mould"
					@click="filters.mould = ''"
					class="text-gray-400 hover:text-red-500 pb-2"
				>
					✕
				</button>
			</div>
			<div class="flex items-end gap-1">
				<SearchSelect label="Item" doctype="Item" v-model="filters.item" />
				<button
					v-if="filters.item"
					@click="filters.item = ''"
					class="text-gray-400 hover:text-red-500 pb-2"
				>
					✕
				</button>
			</div>
			<div class="flex items-end gap-1">
				<SearchSelect label="Shift" doctype="Shift Type" v-model="filters.shift" />
				<button
					v-if="filters.shift"
					@click="filters.shift = ''"
					class="text-gray-400 hover:text-red-500 pb-2"
				>
					✕
				</button>
			</div>

			<!-- MONTH / YEAR -->
			<div>
				<label class="block text-xs text-gray-600">Month</label>
				<input
					type="month"
					v-model="monthPicker"
					class="border rounded px-2 py-1 text-sm"
				/>
			</div>

			<button
				@click="resetFilters"
				class="ml-auto px-4 py-2 text-sm rounded bg-gray-100 hover:bg-gray-200"
			>
				Reset All
			</button>
		</div>

		<!-- CALENDAR -->
		<div class="border rounded bg-white shadow-sm p-1 relative text-black">
			<FullCalendar ref="calendarRef" :options="calendarOptions" class="text-black" />

			<!-- HOVER CARD -->
			<div
				v-if="hoveredEvent"
				class="event-tooltip fixed bg-white border border-gray-200 shadow-xl rounded-lg p-4 w-72 text-sm z-50 text-black"
				:style="{ top: hoverPosition.y + 'px', left: hoverPosition.x + 'px' }"
				@mouseenter="keepTooltipOpen"
				@mouseleave="hideTooltip"
			>
				<div class="font-bold text-base mb-1 text-black">
					<a :href="'/app/work-order/' + hoveredEvent.wo_name">{{
						hoveredEvent.wo_name
					}}</a>
				</div>
				<div class="space-y-1">
					<div class="grid grid-cols-3 gap-1 text-black">
						<span class="text-gray-500 col-span-1">Item:</span>
						<span class="col-span-2 font-medium">{{
							hoveredEvent.production_item
						}}</span>
					</div>
					<div class="grid grid-cols-3 gap-1 text-black">
						<span class="text-gray-500 col-span-1">Qty:</span>
						<span class="col-span-2 font-medium">{{ hoveredEvent.qty || "-" }}</span>
					</div>
					<div class="grid grid-cols-3 gap-1 text-black" v-if="hoveredEvent.sales_order">
						<span class="text-gray-500 col-span-1">SO:</span>
						<span class="col-span-2 font-medium">{{
							hoveredEvent.sales_order || "-"
						}}</span>
					</div>
					<div class="grid grid-cols-3 gap-1 text-black">
						<span class="text-gray-500 col-span-1">Mould:</span>
						<span class="col-span-2 font-medium">{{ hoveredEvent.mould || "-" }}</span>
					</div>
					<div class="grid grid-cols-3 gap-1 text-black">
						<span class="text-gray-500 col-span-1">Machine:</span>
						<span class="col-span-2 font-medium">{{
							hoveredEvent.workstation || "-"
						}}</span>
					</div>
					<div class="grid grid-cols-3 gap-1 text-black">
						<span class="text-gray-500 col-span-1">Status:</span>
						<span class="col-span-2 font-medium">{{
							hoveredEvent.status || "-"
						}}</span>
					</div>
					<div class="border-t pt-1 mt-1 text-xs text-gray-400 text-black">
						<div>
							Start:
							{{ new Date(hoveredEvent.planned_start_date).toLocaleString() || "-" }}
						</div>
						<div>
							End:
							{{ new Date(hoveredEvent.planned_end_date).toLocaleString() || "-" }}
						</div>
					</div>
				</div>
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
	sales_order: "",
	mould: "",
	item: "",
	shift: "",
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
	snapDuration: "00:15:00",
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
	eventResize: handleEventChange,
	eventClick: handleEventClick,
	eventMouseEnter: handleEventMouseEnter,
	eventMouseLeave: handleEventMouseLeave,

	eventContent: (arg) => {
		if (arg.event.display === "background" || !arg.event.extendedProps.wo_name) {
			return null;
		}
		return { html: renderWOCard(arg.event.extendedProps) };
	},
};

/* ---------------- WATCHERS ---------------- */
watch(monthPicker, (val) => {
	const [y, m] = val.split("-").map(Number);
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
	filters.sales_order = "";
	filters.mould = "";
	filters.item = "";
	filters.shift = "";
	// Watcher will trigger loadSchedule
}

/* ---------------- UI ---------------- */
function renderWOCard(wo) {
	return `
    <div class="text-black p-1 rounded border-l-4 ${statusClass(wo.status)}
      bg-gradient-to-br from-blue-50 text-[10px] leading-tight overflow-hidden h-full flex flex-col justify-between" style="color: black !important;">
      <div>
        <div class="font-bold truncate text-black" title="${wo.wo_name}" style="color: black;">${
			wo.wo_name
		}</div>
        <div class="truncate font-semibold text-black" title="${wo.production_item}" style="color: black;">${
			wo.production_item
		}</div>
        <div class="truncate text-black" style="color: black;">Mould: ${wo.mould || "-"}</div>
        <div class="truncate text-black" style="color: black;">WS: ${wo.workstation || "-"}</div>
        <div class="truncate text-black" style="color: black;">SO: ${wo.sales_order || "-"}</div>
      </div>
      <div class="mt-1 font-mono text-xs text-black" style="color: black;">
        ${fmt(wo.planned_start_date)} - ${fmt(wo.planned_end_date)}
      </div>
    </div>
  `;
}

function fmt(dt) {
	if (!dt) return "";
	return new Date(dt).toLocaleTimeString([], {
		hour: "2-digit",
		minute: "2-digit",
	});
}

function statusClass(status) {
	return (
		{
			Draft: "border-blue-500 text-black",
			"In Progress": "border-orange-500 text-black",
			Completed: "border-green-500 text-black",
		}[status] || "border-gray-400 text-black"
	);
}

// onMounted removed to prevent double fetch (datesSet triggers initial load)
</script>

<style scoped>
/* Tooltip styling */
.event-tooltip {
	z-index: 9999;
	/* pointer-events: none; REMOVED to allow hovering over tooltip */
}
div {
	color: black;
}
</style>
