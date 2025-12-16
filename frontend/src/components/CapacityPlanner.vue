<template>
  <div class="capacity-planner p-4 bg-white rounded shadow-sm">
    <div class="flex items-center justify-between mb-3">
      <div>
        <button @click="validateAll" class="px-3 py-1 bg-blue-100 text-black rounded">Validate</button>
        <button @click="computePreview" class="px-3 py-1 bg-indigo-100 text-black rounded ml-2">Preview
          Schedule</button>
        <button @click="planAndCreate" :disabled="!canPlan" class="px-3 py-1 bg-gray-200 text-black rounded ml-2">Plan
          & Create Work Orders</button>
      </div>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-3 text-sm text-gray-600">
      <div>
        Weekend days:
        <label v-for="d in weekendDaysOptions" :key="d.value" class="ml-2">
          <input type="checkbox" v-model="weekendDays" :value="d.value" /> {{ d.label }}
        </label>
      </div>
      <div class="flex items-center space-x-4">
        <div>
          <label>Production Utilization (%):</label>
          <input type="number" v-model="productionUtilization" class="ml-2 border rounded px-2 py-1 w-20" />
        </div>
        <div>
          <label>Plan Start Date:</label>
          <input type="date" v-model="planStartDate" class="ml-2 border rounded px-2 py-1" />
        </div>
        <div>
          <label>Plan End Date:</label>
          <input type="date" v-model="planEndDate" class="ml-2 border rounded px-2 py-1" />
        </div>
      </div>
    </div>

    <div v-if="!localBoms.length" class="text-gray-500">No BOMs selected.</div>

    <div v-for="(bom, idx) in capacityPlanData" :key="bom.bom_no" class="mb-4 border rounded p-3">
      <h3 class="font-bold text-md">{{ bom.item_code }} ({{ bom.bom_no }})</h3>
      <div class="text-sm text-gray-500">Required Qty: {{ bom.required_for_selected_qty }}</div>

      <div class="mt-3 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
        <div>Machine: <strong>{{ bom.selected_workstation || 'N/A' }}</strong></div>
        <div>Cycle Time: <strong>{{ bom.cycle_time }}s</strong></div>
        <div>Cavity: <strong>{{ bom.cavity }}</strong></div>
        <div>Hourly Capacity: <strong>{{ bom.machineHourlyCapacity }} pcs</strong></div>
        <div>Hrs Required: <strong>{{ bom.hrsRequired }} hrs</strong></div>
        <div>Month Capacity: <strong>{{ bom.monthCapacityHrs }} hrs</strong></div>
        <div>Balance: <strong :class="{ 'text-red-500': bom.balanceHrs < 0 }">{{ bom.balanceHrs }} hrs</strong></div>
        <div>Overload: <strong class="text-red-500">{{ bom.overloadHrs }} hrs</strong></div>
        <div>Working Days: <strong>{{ bom.workingDays }}</strong></div>
        <div>Shifts per Day: <strong>{{ bom.shiftsPerDay }}</strong></div>
        <div>Daily Capacity: <strong>{{ bom.dailyCapacityHrs }} hrs</strong></div>
        <div>Required Shifts: <strong>{{ bom.requiredShifts }}</strong></div>
      </div>

      <div class="mt-2">
        <div v-if="bom.validation_error" class="text-red-600 text-sm">{{ bom.validation_error }}</div>
        <div v-else class="text-green-600 text-sm">OK — capacity sufficient for selected month.</div>
      </div>

      <div v-if="preview[bom.bom_no]" class="mt-3">
        <div class="text-sm font-medium">Schedule Preview </div>
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
  capBoms: { type: Array, default: () => [] },
  filters: { type: Object, default: () => ({}) },
  availableMachineHours: { type: Object, default: () => ({}) }
});
const emit = defineEmits(['capacity-updated']);

const localBoms = ref([]);
const machines = ref([]);
const shifts = ref([]);
const preview = ref({});

const weekendDaysOptions = [
  { value: 0, label: 'Sun' },
  { value: 6, label: 'Sat' },
];
const weekendDays = ref([0, 6]);
const productionUtilization = ref(90);
const planStartDate = ref(null);
const planEndDate = ref(null);

onMounted(async () => {
  syncLocalBoms();
  const ws = await api.getWorkstations();
  machines.value = Array.isArray(ws) ? ws : [];
  try {
    const shift_types = await api.getShifts();
    shifts.value = Array.isArray(shift_types) ? shift_types : [];
  } catch (e) {
    console.error('Error fetching shifts', e);
  }
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
    validation_error: null,
    sales_order: b.sales_order
  }));
  preview.value = {};
}

const capacityPlanData = computed(() => {
  return localBoms.value.map(bom => {
    const machine = machines.value.find(m => m.name === bom.selected_workstation);

    const requiredQty = Number(bom.required_for_selected_qty) || 0;
    const cycleTime = Number(bom.cycle_time) || 0;
    const cavity = Math.max(1, Number(bom.cavity) || 1);

    const perPieceSec = cycleTime / cavity;
    const machineHourlyCapacity = perPieceSec > 0 ? 3600 / perPieceSec : 0;
    const hrsRequired = machineHourlyCapacity > 0 ? requiredQty / machineHourlyCapacity : 0;

    const year = new Date(bom.month).getFullYear();
    const month = new Date(bom.month).getMonth();
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    let workingDays = 0;
    for (let i = 1; i <= daysInMonth; i++) {
      const day = new Date(year, month, i).getDay();
      if (!weekendDays.value.includes(day)) {
        workingDays++;
      }
    }

    const shiftsPerDay = shifts.value.length || bom.shifts_per_day || machine?.shifts_per_day || 2;
    const totalShiftHours = shifts.value.reduce((acc, s) => {
      if (!s.start_time || !s.end_time) return acc;
      const start = new Date(`1970-01-01T${s.start_time}`);
      const end = new Date(`1970-01-01T${s.end_time}`);
      let diff = (end - start) / 3600000;
      if (diff <= 0) diff += 24;
      return acc + diff;
    }, 0);

    const dailyCapacityHrs = shifts.value.length ? totalShiftHours : (shiftsPerDay * (bom.shift_hours || machine?.shift_hours || 8));
    const avgShiftHours = shiftsPerDay > 0 ? dailyCapacityHrs / shiftsPerDay : (bom.shift_hours || machine?.shift_hours || 8);

    const monthCapacityHrs = workingDays * dailyCapacityHrs * (productionUtilization.value / 100);

    const balanceHrs = monthCapacityHrs - hrsRequired;
    const overloadHrs = balanceHrs < 0 ? Math.abs(balanceHrs) : 0;

    const utilizedShiftHours = avgShiftHours * (productionUtilization.value / 100);
    const requiredShifts = utilizedShiftHours > 0 ? hrsRequired / utilizedShiftHours : 0;

    return {
      ...bom,
      machineHourlyCapacity: machineHourlyCapacity.toFixed(2),
      hrsRequired: hrsRequired.toFixed(2),
      monthDays: daysInMonth,
      workingDays: workingDays,
      shiftsPerDay: shiftsPerDay,
      dailyCapacityHrs: dailyCapacityHrs,
      monthCapacityHrs: monthCapacityHrs.toFixed(2),
      balanceHrs: balanceHrs.toFixed(2),
      overloadHrs: overloadHrs.toFixed(2),
      requiredShifts: requiredShifts.toFixed(2)
    };
  });
});

const totalRequiredHours = computed(() =>
  capacityPlanData.value.reduce((sum, b) => sum + Number(b.hrsRequired), 0)
);

const totalPlannedCapacity = computed(() =>
  capacityPlanData.value.reduce((sum, b) => sum + Number(b.monthCapacityHrs), 0)
);

async function validateAll() {
  localBoms.value.forEach(b => {
    if (!b.selected_workstation) b.validation_error = "Please select a workstation";
  });

  const payload = {
    production_utilization: productionUtilization.value,
    lines: localBoms.value.map(b => ({
      bom_no: b.bom_no,
      fg_item: b.item_code,
      schedule_qty: b.required_for_selected_qty,
      month: b.month,
      machine: b.selected_workstation,
    }))
  };


  try {
    const res = await api.validate_capacity(payload);
    const results = res.data.message; // <- access the returned array
    if (Array.isArray(results)) {
      results.forEach(r => {
        const bom = localBoms.value.find(x => x.bom_no === r.bom_no);
        if (bom) bom.validation_error = r.ok ? null : r.message;
      });
    }


    emit('capacity-updated', { boms: localBoms.value });
  } catch (err) {
    console.error("Capacity validation failed", err);
  }
}


const computePreview = () => {
  preview.value = {};
  capacityPlanData.value.forEach(b => {
    const shift_hours = b.shift_hours || 8;
    const shifts_per_day = b.shifts_per_day || 2;
    const perHourPieces = b.machineHourlyCapacity || 0;
    const shiftCapacity = perHourPieces * shift_hours * (productionUtilization.value / 100);
    let remaining = b.required_for_selected_qty || 0;
    const schedule = [];

    if (planStartDate.value) {
      let current = new Date(planStartDate.value);
      const end = planEndDate.value ? new Date(planEndDate.value) : new Date(current.getFullYear(), current.getMonth() + 1, 0);

      while (current <= end && remaining > 0) {
        if (!weekendDays.value.includes(current.getDay())) {
          for (let s = 1; s <= shifts_per_day && remaining > 0; s++) {
            const allocate = Math.min(shiftCapacity, remaining);
            schedule.push({ day: current.toISOString().slice(0, 10), shift: s, qty: allocate });
            remaining -= allocate;
          }
        }
        current.setDate(current.getDate() + 1);
      }
    }

    if (remaining > 0) schedule.push({ day: "overflow", shift: 0, qty: remaining });
    preview.value[b.bom_no] = schedule;
  });
};


const canPlan = computed(() => {
  return localBoms.value.length > 0 && localBoms.value.every(b => !b.validation_error && b.selected_workstation && b.required_for_selected_qty > 0);
});

async function planAndCreate() {
  computePreview();
  const payload = {
    lines: capacityPlanData.value.map(b => ({
      bom_no: b.bom_no,
      sales_order: b.sales_order,
      fg_item: b.item_code,
      schedule_qty: b.required_for_selected_qty,
      month: b.month,
      machine: b.selected_workstation,
      working_days: b.workingDays,
      shifts_per_day: b.shifts_per_day,
      shift_hours: b.shift_hours,
      cycle_time: b.cycle_time,
      cavity: b.cavity,
      related_bso: b.related_bso || null,
      schedule: preview.value[b.bom_no] || [],
      customer: b.customer

    })),
    filters: props.filters,
    plan_start_date: planStartDate.value,
    plan_end_date: planEndDate.value,
    production_utilization: productionUtilization.value
  };

  const res = await api.createMSSPlan(payload);
  if (res.data.success) {
    alert(`Created WOs: ${res.data.created_work_orders.length}`);
    preview.value = {};
  }
}

</script>
<style>
/* only custom overrides here */
</style>
