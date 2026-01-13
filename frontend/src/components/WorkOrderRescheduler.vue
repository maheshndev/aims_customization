<template>
  <div class="p-3 space-y-3">

    <!-- FILTER BAR -->
    <div class="flex flex-wrap items-end gap-3 bg-white p-3 rounded shadow-sm">

      <div class="flex items-end gap-1">
        <SearchSelect label="Sales Order" doctype="Sales Order" v-model="filters.sales_order" />
        <button v-if="filters.sales_order" @click="filters.sales_order = ''" class="text-gray-400 hover:text-red-500 pb-2">✕</button>
      </div>
      <div class="flex items-end gap-1">
        <SearchSelect label="Mould" doctype="Mould" v-model="filters.mould" />
        <button v-if="filters.mould" @click="filters.mould = ''" class="text-gray-400 hover:text-red-500 pb-2">✕</button>
      </div>
      <div class="flex items-end gap-1">
        <SearchSelect label="Item" doctype="Item" v-model="filters.item" />
        <button v-if="filters.item" @click="filters.item = ''" class="text-gray-400 hover:text-red-500 pb-2">✕</button>
      </div>
      <div class="flex items-end gap-1">
        <SearchSelect label="Shift" doctype="Shift Type" v-model="filters.shift" />
        <button v-if="filters.shift" @click="filters.shift = ''" class="text-gray-400 hover:text-red-500 pb-2">✕</button>
      </div>

      <!-- MONTH / YEAR -->
      <div>
        <label class="block text-xs text-gray-600">Month</label>
        <input type="month" v-model="monthPicker"
          class="border rounded px-2 py-1 text-sm" />
      </div>

      <button
        @click="resetFilters"
        class="ml-auto px-4 py-2 text-sm rounded bg-gray-100 hover:bg-gray-200"
      >
        Reset All
      </button>
    </div>

    <!-- CALENDAR -->
    <div class="border rounded bg-white shadow-sm p-2">
      <FullCalendar ref="calendarRef" :options="calendarOptions" />
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

/* ---------------- STATE ---------------- */
const calendarRef = ref(null);
const schedule = ref([]);
const holidays = ref([]);

const filters = reactive({
  sales_order: "",
  mould: "",
  item: "",
  shift: ""
});

/* ---------------- MONTH PICKER ---------------- */
const today = new Date();
const monthPicker = ref(
  `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}`
);

/* ---------------- CALENDAR RANGE (SOURCE OF TRUTH) ---------------- */
const visibleRange = reactive({
  from: null,
  to: null
});

/* ---------------- API PAYLOAD ---------------- */
const apiPayload = computed(() => ({
  from_date: visibleRange.from,
  to_date: visibleRange.to,
  ...filters
}));

/* ---------------- EVENTS ---------------- */
function buildEvents() {
  const woEvents = schedule.value.map(wo => ({
    id: wo.wo_name,
    title: wo.wo_name,
    start: wo.planned_start_date,
    end: wo.planned_end_date,
    allDay: false,
    editable: wo.status === "Draft",
    extendedProps: wo
  }));

  const holidayEvents = holidays.value.map(h => ({
    title: h.description,
    start: h.holiday_date,
    allDay: true,
    display: 'background',
    color: '#ff9f89' // Light red for holidays
  }));

  return [...woEvents, ...holidayEvents];
}

/* ---------------- DATE FORMATTER ---------------- */
function toLocalString(date) {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, '0');
  const d = String(date.getDate()).padStart(2, '0');
  const h = String(date.getHours()).padStart(2, '0');
  const min = String(date.getMinutes()).padStart(2, '0');
  const s = String(date.getSeconds()).padStart(2, '0');
  return `${y}-${m}-${d} ${h}:${min}:${s}`;
}

async function handleEventChange(info) {
  try {
    const { start, end } = info.event;
    
    // Calculate newEnd if missing, using old duration if available
    let newEnd = end;
    if (!newEnd && info.oldEvent && info.oldEvent.end) {
        const duration = info.oldEvent.end - info.oldEvent.start;
        newEnd = new Date(start.getTime() + duration);
    }
    const safeEnd = newEnd || new Date(start.getTime() + 60 * 60 * 1000); // Fallback 1h

    await mssApi.reschedule({
      wo_name: info.event.id,
      planned_start_date: toLocalString(start),
      planned_end_date: toLocalString(safeEnd)
    });
    
    // Refresh to get any server-side adjustments (holidays, etc.)
    await loadSchedule();
  } catch (e) {
    info.revert();
    console.error("Reschedule failed", e);
    
    // Parse Frappe Error Message
    let msg = "Failed to reschedule.";
    if (e.response && e.response.data) {
        const d = e.response.data;
        if (d._server_messages) {
             try {
                 const messages = JSON.parse(d._server_messages);
                 msg = messages.map(m => JSON.parse(m).message).join("<br>");
             } catch (err) { /* ignore parse error */ }
        } else if (d.exception) {
            msg = d.exception;
        }
    }
    
    // Show Alert to User
    if (window.frappe) {
        frappe.msgprint({
            title: 'Reschedule Failed',
            message: msg,
            indicator: 'red'
        });
    } else {
        alert(msg.replace(/<br>/g, "\n"));
    }
  }
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
  nextDayThreshold: '00:00:00', 
  
  // Visual style
  eventDisplay: 'block',
  displayEventTime: true,
  
  headerToolbar: {
    left: "prev,next today",
    center: "title",
    right: "dayGridMonth,timeGridWeek"
  },

  events(fetchInfo, successCallback) {
    // We supply events manually via schedule.value watching
    // But FullCalendar needs a function or array. 
    // We'll return the buildEvents() result.
    successCallback(buildEvents());
  },

  datesSet(info) {
    visibleRange.from = info.startStr;
    visibleRange.to = new Date(info.end.getTime() - 1)
      .toISOString()
      .slice(0, 10);

    loadSchedule();
  },

  eventDrop: handleEventChange,
  eventResize: handleEventChange,

  eventContent: arg => ({
    html: renderWOCard(arg.event.extendedProps)
  })
};

/* ---------------- WATCHERS ---------------- */
watch(monthPicker, val => {
  const [y, m] = val.split("-").map(Number);
  calendarRef.value?.getApi().gotoDate(new Date(y, m - 1, 1));
});

// Auto-refresh when filters change
watch(filters, () => {
    loadSchedule();
}, { deep: true });

// Refetch events when schedule changes
watch(schedule, () => {
    calendarRef.value?.getApi().refetchEvents();
});

/* ---------------- API ---------------- */
async function loadSchedule() {
  if (!visibleRange.from || !visibleRange.to) return;
  // Optimize: Check if we are already loading or if request is identical? 
  // For now, relies on simple debouncing or just letting it fly, but removing onMounted helps.
  
  try {
      const [res, holRes] = await Promise.all([
          mssApi.load(apiPayload.value),
          mssApi.getHolidays(visibleRange.from, visibleRange.to)
      ]);
      
      schedule.value = res.data.message || [];
      holidays.value = holRes.data.message || [];
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
    <div class="p-1 rounded border-l-4 ${statusClass(wo.status)}
      bg-gradient-to-br from-blue-50 to-white text-[10px] leading-tight overflow-hidden h-full flex flex-col justify-between">
      <div>
        <div class="font-bold truncate text-indigo-700" title="${wo.wo_name}">${wo.wo_name}</div>
        <div class="truncate font-semibold" title="${wo.production_item}">${wo.production_item}</div>
        <div class="truncate text-gray-600">Mould: ${wo.mould || "-"}</div>
        <div class="truncate text-gray-600">WS: ${wo.workstation || "-"}</div>
        <div class="truncate text-gray-600">SO: ${wo.sales_order || "-"}</div>
      </div>
      <div class="mt-1 font-mono text-xs">
        ${fmt(wo.planned_start_date)} - ${fmt(wo.planned_end_date)}
      </div>
    </div>
  `;
}

function fmt(dt) {
  if (!dt) return "";
  return new Date(dt).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit"
  });
}

function statusClass(status) {
  return {
    Draft: "border-blue-500",
    "In Progress": "border-orange-500",
    Completed: "border-green-500"
  }[status] || "border-gray-400";
}

// onMounted removed to prevent double fetch (datesSet triggers initial load)
</script>
