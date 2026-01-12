<template>
  <div class="p-3 space-y-3">

    <!-- FILTER BAR -->
    <div class="flex flex-wrap items-end gap-3 bg-white p-3 rounded shadow-sm">

      <SearchSelect label="Sales Order" doctype="Sales Order" v-model="filters.sales_order" />
      <SearchSelect label="Mould" doctype="Mould" v-model="filters.mould" />
      <SearchSelect label="Item" doctype="Item" v-model="filters.item" />
      <SearchSelect label="Shift" doctype="Shift Type" v-model="filters.shift" />

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
  return schedule.value.map(wo => ({
    id: wo.wo_name,
    title: wo.wo_name,
    start: wo.planned_start_date,
    end: wo.planned_end_date,
    editable: wo.status === "Draft",
    extendedProps: wo
  }));
}


/* ---------------- CALENDAR OPTIONS ---------------- */
const calendarOptions = {
  plugins: [dayGridPlugin, timeGridPlugin, interactionPlugin],
  initialView: "dayGridMonth",
  height: "auto",
  editable: true,

  headerToolbar: {
    left: "prev,next today",
    center: "title",
    right: "dayGridMonth,timeGridWeek"
  },

  events(fetchInfo, successCallback) {
    successCallback(buildEvents());
  },

  datesSet(info) {
    visibleRange.from = info.startStr;
    visibleRange.to = new Date(info.end.getTime() - 1)
      .toISOString()
      .slice(0, 10);

    loadSchedule();
  },

  eventDrop: async info => {
  await mssApi.reschedule({
    wo_name: info.event.id,
    planned_start_date: info.event.start.toISOString(),
    planned_end_date: info.event.end.toISOString()
  });
},



  eventContent: arg => ({
    html: renderWOCard(arg.event.extendedProps)
  })
};


/* ---------------- WATCH MONTH PICKER ---------------- */
watch(monthPicker, val => {
  const [y, m] = val.split("-").map(Number);
  calendarRef.value?.getApi().gotoDate(new Date(y, m - 1, 1));
});

/* ---------------- API ---------------- */
async function loadSchedule() {
  if (!visibleRange.from || !visibleRange.to) return;

  const res = await mssApi.load(apiPayload.value);
  schedule.value = res.data.message || [];
}

/* ---------------- RESET ---------------- */
function resetFilters() {
  Object.keys(filters).forEach(k => (filters[k] = ""));
  loadSchedule();
}

/* ---------------- UI ---------------- */
function renderWOCard(wo) {
  return `
    <div class="p-2 rounded border-l-4 ${statusClass(wo.status)}
      bg-gradient-to-br from-blue-50 to-white text-xs space-y-1">
      <div class="font-semibold">${wo.wo_name}</div>
      <div>SO: ${wo.sales_order || "-"}</div>
      <div>Mould: ${wo.mould || "-"}</div>
      <div>${fmt(wo.planned_start_date)} – ${fmt(wo.planned_end_date)}</div>
    </div>
  `;
}

function fmt(dt) {
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

onMounted(loadSchedule);
</script>
