<template>
  <div class="capacity-planner p-4 bg-white rounded shadow-sm">
    <div class="flex items-center justify-between mb-3">
      <div>
        <button @click="validateAll" class="px-3 py-1 bg-blue-600 text-black rounded">Validate</button>
        <button @click="computePreview" class="px-3 py-1 bg-indigo-600 text-black rounded ml-2">Preview
          Schedule</button>
        <button @click="planAndCreate" :disabled="!canPlan" class="px-3 py-1 bg-green-600 text-black rounded ml-2">Plan
          & Create Work Orders</button>
      </div>
    </div>

    <div class="mb-3 text-sm text-gray-600">
      Weekend days:
      <label v-for="d in weekendDaysOptions" :key="d.value" class="ml-2">
        <input type="checkbox" v-model="weekendDays" :value="d.value" /> {{ d.label }}
      </label>
    </div>

    <div v-if="!localBoms.length" class="text-gray-500">No BOMs selected.</div>

    <div v-for="(bom, idx) in localBoms" :key="bom.bom_no" class="mb-4 border rounded p-3">
      <!-- same UI as before ... -->
      <div class="mt-3 grid grid-cols-4 gap-4 text-sm">
        <div>Cycle Time (s/shot): <strong>{{ bom.cycle_time || '—' }}</strong></div>
        <div>No. of cavity: <strong>{{ bom.cavity || '—' }}</strong></div>
        <div>Cycle Time per piece (s): <strong>{{ cycleSecPerPiece(bom) }}</strong></div>
        <div>Required Hours: <strong>{{ requiredHours(bom) }}</strong></div>
      </div>

      <div class="mt-2">
        <div v-if="bom.validation_error" class="text-red-600 text-sm">{{ bom.validation_error }}</div>
        <div v-else class="text-green-600 text-sm">OK — capacity sufficient for selected month.</div>
      </div>

      <!-- Schedule preview (simple) -->
      <div v-if="preview[bom.bom_no]" class="mt-3">
        <div class="text-sm font-medium">Schedule Preview (first 7 shifts)</div>
        <div class="text-xs text-gray-600">Format: Day-Shift → qty</div>
        <div class="flex gap-2 mt-1 flex-wrap">
          <div v-for="(s, i) in preview[bom.bom_no].slice(0, 14)" :key="i"
            class="px-2 py-1 border rounded text-xs bg-gray-50">
            {{ s.day }}-S{{ s.shift }} → {{ Math.round(s.qty) }}
          </div>
        </div>
      </div>
    </div>

    <div class="mt-4">
      <div class="text-sm">Summary: Total Required Hours: <strong>{{ totalRequiredHours.toFixed(2) }} hrs</strong></div>
      <div class="text-sm">Total Planned Capacity: <strong>{{ totalPlannedCapacity.toFixed(2) }} hrs</strong></div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue';
import { api } from '../services/api';

const props = defineProps({
         // for selected BOMs numbers
  capBoms: { type: Array, default: () => [] },    // full BOM objects with operations
  filters: { type: Object, default: () => ({}) },
  availableMachineHours: { type: Object, default: () => ({}) }
});
const emit = defineEmits(['capacity-updated']);

const localBoms = ref([]);
const machines = ref([]);
const preview = ref({}); // schedule preview per bom

// weekend options (0=Sun ... 6=Sat)
const weekendDaysOptions = [
  { value: 0, label: 'Sun' },
  { value: 6, label: 'Sat' },
];
const weekendDays = ref([0, 6]); // default Sat+Sun

onMounted(async () => {
  syncLocalBoms();
  const ws = await api.getWorkstations();
  machines.value = Array.isArray(ws) ? ws : [];
});



watch(() => props.capBoms, () => syncLocalBoms(), { deep: true, immediate: true });

function syncLocalBoms() {
 
  
  localBoms.value = (props.capBoms || []).map(b => ({
    ...b,
    month: b.month || (new Date()).toISOString().slice(0, 7),
    schedule_qty: b.required_for_selected_qty || 0,
    selected_workstation: b.selected_workstation || '',
    working_days: b.working_days || 22,
    shifts_per_day: b.shifts_per_day || 2,
    shift_hours: b.shift_hours || 8,
    cycle_time: b.cycle_time || b.cycle_time_from_item || 0,
    cavity: b.cavity || b.cavity_from_item || 1,
    validation_error: null
  }));
  preview.value = {};
}




// helpers (same as before)
function cycleSecPerPiece(bom) {
  const ct = Number(bom.cycle_time) || 0;
  const cav = Number(bom.cavity) || 1;
  if (!ct || !cav) return '—';
  return (ct / cav).toFixed(3);
}
function requiredHours(bom) {
  const perPieceSec = Number(bom.cycle_time || 0) / (Number(bom.cavity || 1) || 1);
  const seconds = Number(bom.required_for_selected_qty || 0) * perPieceSec;
  return seconds / 3600;
}
const totalRequiredHours = computed(() => localBoms.value.reduce((s, b) => s + requiredHours(b), 0));
const totalPlannedCapacity = computed(() =>
  localBoms.value.reduce((sum, b) => {
    if (!Array.isArray(machines.value)) return sum;
    const machine = machines.value.find(m => m.name === b.selected_workstation);
    if (!machine) return sum;
    return sum + Number(machine.monthly_capacity_hours || (b.working_days * b.shifts_per_day * b.shift_hours) || 0);
  }, 0)
);

// validateAll will also ask backend for current allocated hours (so we can check)
async function validateAll() {
  // ensure machine is selected for all BOMs
  localBoms.value.forEach(b => {
    if (!b.selected_workstation) b.validation_error = "Please select a workstation";
  });
 


  const payload = {
    lines: localBoms.value.map(b => ({
      bom_no: b.bom_no,
      fg_item: b.item_code,
      schedule_qty: b.required_for_selected_qty,
      month: b.month,
      machine: b.selected_workstation
    }))
  };

  try {
    const res = await api.validate_capacity(payload);

    // correct field
    res.data.message.forEach(r => {
      const bom = localBoms.value.find(x => x.bom_no === r.bom_no);
      if (bom) {
        bom.validation_error = r.ok ? null : r.message;
      }
    });
    emit('capacity-updated', { boms: localBoms.value });
  } catch (err) {
    console.error(err);
  }
}


// build preview schedule per BOM using shift capacity (client-side preview)
function computePreview() {
  preview.value = {};
  for (const bom of localBoms.value) {
    if (!bom.selected_workstation || !bom.required_for_selected_qty) {
      preview.value[bom.bom_no] = [];
      continue;
    }
    const machine = machines.value.find(m => m.name === bom.selected_workstation);
    const shift_hours = bom.shift_hours || machine?.shift_hours || 8;
    const shifts_per_day = bom.shifts_per_day || machine?.shifts_per_day || 1;
    const working_days = bom.working_days || machine?.working_days || 22;

    // throughput per hour (pieces)
    const perPieceSec = (Number(bom.cycle_time || 0) / Math.max(1, Number(bom.cavity || 1)));
    const perHourPieces = perPieceSec > 0 ? Math.floor(3600.0 / perPieceSec) : 0;

    const shiftCapacityPieces = Math.floor(perHourPieces * shift_hours);
    const total_shifts = working_days * shifts_per_day;

    // simple queue allocation: fill shifts up to shiftCapacityPieces
    let remaining = Math.round(bom.required_for_selected_qty || 0);
    const schedule = [];
    let day = 1;
    for (let d = 0; d < working_days && remaining > 0; d++) {
      for (let s = 1; s <= shifts_per_day && remaining > 0; s++) {
        const allocate = Math.min(shiftCapacityPieces, remaining);
        schedule.push({ day: d + 1, shift: s, qty: allocate });
        remaining -= allocate;
      }
    }
    // if remaining > 0, creates overflow entries (will go to next month / queued)
    if (remaining > 0) {
      schedule.push({ day: 'overflow', shift: 0, qty: remaining });
    }
    preview.value[bom.bom_no] = schedule;
  }
  // emit preview so parent can display if needed
  emit('capacity-updated', { boms: localBoms.value, preview: preview.value });
}

// when machine changes: re-validate and compute preview
async function onMachineChange(bom) {
  const machine = machines.value.find(m => m.name === bom.selected_workstation);
  if (machine) {
    bom.shift_hours = bom.shift_hours || machine.shift_hours || bom.shift_hours;
    bom.working_days = bom.working_days || machine.working_days || bom.working_days;
    bom.shifts_per_day = bom.shifts_per_day || machine.shifts_per_day || bom.shifts_per_day;
  }
  await validateAll();
  computePreview();
}

const canPlan = computed(() => {
  return localBoms.value.length > 0 && localBoms.value.every(b => !b.validation_error && b.selected_workstation && b.required_for_selected_qty > 0);
});

// Plan & Create (send preview and lines to backend)
async function planAndCreate() {
  // Build payload with shift allocations if preview exists
  // If preview empty, compute one
  computePreview();

  const lines = localBoms.value.map(b => ({
    bom_no: b.bom_no,
    fg_item: b.item_code,
    schedule_qty: b.required_for_selected_qty,
    month: b.month,
    machine: b.selected_workstation,
    working_days: b.working_days,
    shifts_per_day: b.shifts_per_day,
    shift_hours: b.shift_hours,
    cycle_time: b.cycle_time,
    cavity: b.cavity,
    related_bso: b.related_bso || null,
    schedule: (preview.value[b.bom_no] || []).map(s => ({ day: s.day, shift: s.shift, qty: s.qty }))
  }));

  try {
    const res = await api.createMSSPlan({ lines, filters: props.filters });
    // server returns created SOs and WOs
    emit('capacity-updated', { created: res.data });
  } catch (err) {
    console.error(err);
  }
}
</script>
