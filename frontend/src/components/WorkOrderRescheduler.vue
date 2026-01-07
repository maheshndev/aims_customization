<template>
  <div class="p-4 space-y-4">
    <!-- CONTROLS -->
    <div class="flex items-end gap-4 bg-white p-3 rounded shadow">
      <div>
        <label class="block text-xs text-gray-600">From</label>
        <input type="date" v-model="fromDate" class="border rounded px-2 py-1" />
      </div>

      <div>
        <label class="block text-xs text-gray-600">To</label>
        <input type="date" v-model="toDate" class="border rounded px-2 py-1" />
      </div>

      <button
        @click="loadSchedule"
        class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
      >
        Load MSS
      </button>

      <span class="ml-auto font-semibold text-gray-700">
        {{ fromDate }} → {{ toDate }}
      </span>
    </div>

    <!-- TIMELINE -->
    <div class="border rounded overflow-hidden bg-white shadow">
      <FullCalendar ref="calendarRef" :options="calendarOptions" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, reactive, onMounted, nextTick } from "vue";
import FullCalendar from "@fullcalendar/vue3";
import dayGridPlugin from "@fullcalendar/daygrid";
import timeGridPlugin from "@fullcalendar/timegrid";
import resourceTimelinePlugin from "@fullcalendar/resource-timeline";
import interactionPlugin from "@fullcalendar/interaction";
import { mssApi } from "../services/rescheduleApi";

// ---------------- STATE ----------------
const calendarRef = ref(null);
const schedule = ref([]);

const today = new Date();
const fromDate = ref(today.toISOString().slice(0, 10));
const toDate = ref(
  new Date(today.setDate(today.getDate() + 7)).toISOString().slice(0, 10)
);

// ---------------- COMPUTED ----------------
const resources = computed(() => {
  const set = new Set();
  schedule.value.forEach(wo => wo.workstations.forEach(ws => set.add(ws)));
  return [...set].map(ws => ({ id: ws, title: ws }));
});

const events = computed(() =>
  schedule.value.map(wo => ({
    id: wo.wo_name,
    title: wo.wo_name,
    start: wo.planned_start_date,
    end: wo.planned_end_date,
    resourceId: wo.workstations[0],
    extendedProps: {
      production_item: wo.production_item,
      sales_order: wo.sales_order,
      fg_item: wo.fg_item,
      qty: wo.qty,
      mould:wo.mould,
    }
  }))
);

// ---------------- CALENDAR OPTIONS ----------------
const calendarOptions = reactive({
  plugins: [dayGridPlugin, timeGridPlugin, resourceTimelinePlugin, interactionPlugin],
  initialView: "dayGridMonth",
  editable: true,
  headerToolbar: {
    left: "prev,next today",
    center: "title",
    right: "dayGridMonth,timeGridWeek,timeGridDay"
  },
  height: "auto",
  timeZone: "local",
  slotMinTime: "06:00:00",
  slotMaxTime: "22:00:00",
  resources: computed(() => resources.value),
  events: computed(() => events.value),
  eventDrop: async info => {
    try {
      await mssApi.reschedule({
        wo_name: info.event.id,
        target_datetime: info.event.start.toISOString()
      });
      await loadSchedule();
    } catch (err) {
      info.revert();
      alert(err.response?.data?.message || err.message);
    }
  },
  eventContent: arg => {
    return {
      html: `
        <div class="p-1 rounded bg-blue-100 border-l-4 border-blue-600 text-xs">
          <div class="font-bold truncate">${arg.event.title}</div>
          <div class="truncate">SO: ${arg.event.extendedProps.sales_order}</div>
          <div class="truncate">${arg.event.extendedProps.production_item}</div>
          <div class="truncate">${arg.event.extendedProps.mould}</div>
          <div class="truncate">${arg.event.id}</div>
          <div class="truncate">${formatTime(arg.event.start)} - ${formatTime(arg.event.end)}</div>
          
         
        </div>
      `
    };
  }
});

// ---------------- METHODS ----------------
async function loadSchedule() {
  const res = await mssApi.load(fromDate.value, toDate.value);
  schedule.value = res.data.message || [];

  // Wait for next tick to ensure calendar is mounted
  await nextTick();
  if (calendarRef.value?.getApi) {
    calendarRef.value.getApi().gotoDate(fromDate.value);
  }
}

function formatTime(dt) {
  return new Date(dt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", hour12: false });
}

// ---------------- MOUNT ----------------
onMounted(loadSchedule);
</script>
