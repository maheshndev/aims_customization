<template>
  <div class="capacity-planner p-4 bg-white rounded shadow-sm">

    <!-- Actions -->
    <div class="flex items-center justify-between mb-4">
      <div class="flex gap-2">
        <button
          class="px-3 py-1 bg-blue-100 rounded"
          @click="validateAll"
        >
          Validate Capacity
        </button>

        <button
          class="px-3 py-1 bg-indigo-100 rounded"
          @click="computePreview"
        >
          Preview Schedule
        </button>

        <button
          class="px-3 py-1 bg-green-200 rounded"
          :disabled="!canPlan"
          @click="planAndCreate"
        >
          Plan & Create Work Orders
        </button>
      </div>

      <div class="flex gap-4 text-sm">
        <div>
          <label class="mr-1">Utilization %</label>
          <input
            type="number"
            v-model.number="productionUtilization"
            class="border px-2 py-1 w-20 rounded"
            min="1"
            max="100"
          />
        </div>

        <div>
          <label class="mr-1">Plan Start</label>
          <input
            type="date"
            v-model="planStartDate"
            class="border px-2 py-1 rounded"
          />
        </div>

        <div>
          <label class="mr-1">Plan End</label>
          <input
            type="date"
            v-model="planEndDate"
            class="border px-2 py-1 rounded"
          />
        </div>
      </div>
    </div>

    <div v-if="!localBoms.length" class="text-gray-500">
      No BOMs selected
    </div>

    <!-- BOM CARDS -->
    <div
      v-for="b in capacityData"
      :key="b.bom_no"
      class="border rounded p-3 mb-4"
    >
      <h3 class="font-semibold">
        {{ b.item_code }} — {{ b.bom_no }}
      </h3>

      <div class="text-sm text-gray-600">
        Required Qty: {{ b.schedule_qty }}
      </div>

      <div class="grid grid-cols-2 md:grid-cols-4 gap-3 mt-3 text-sm">
        <div>Workstation: <b>{{ b.machine }}</b></div>
        <div>Mould: <b>{{ b.mould || "—" }}</b></div>
        <div>Cycle Time: <b>{{ b.cycle_time }} sec</b></div>
        <div>Cavity: <b>{{ b.cavity }}</b></div>

        <div>Pcs / Hour: <b>{{ b.pcs_per_hour }}</b></div>
        <div>Shift Hours: <b>{{ b.shift_hours }}</b></div>
        <div>Pcs / Shift: <b>{{ b.pcs_per_shift }}</b></div>
        <div>Required Shifts: <b>{{ b.required_shifts }}</b></div>
      </div>

      <div class="mt-2 text-sm">
        Required Hours:
        <b>{{ b.required_hours }}</b> /
        Monthly Capacity:
        <b>{{ b.month_capacity }}</b>
      </div>

      <div v-if="b.validation_error" class="text-red-600 text-sm mt-1">
        {{ b.validation_error }}
      </div>

      <div v-else class="text-green-600 text-sm mt-1">
        Capacity OK
      </div>

      <!-- Preview -->
      <div v-if="preview[b.bom_no]" class="mt-3">
        <div class="font-medium text-sm">Schedule Preview</div>
        <div class="flex flex-wrap gap-2 mt-1">
          <div
            v-for="(p, i) in preview[b.bom_no]"
            :key="i"
            class="px-2 py-1 border rounded text-xs bg-gray-50"
          >
            {{ p.date }} | Shift {{ p.shift }} → {{ p.qty }}
          </div>
        </div>
      </div>
    </div>

    <!-- Summary -->
    <div class="mt-4 text-sm">
      <div>Total Required Hours: <b>{{ totalRequiredHours }}</b></div>
      <div>Total Monthly Capacity: <b>{{ totalMonthlyCapacity }}</b></div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from "vue"
import { api } from "../services/api"

/* ---------------- PROPS ---------------- */
const props = defineProps({
  capBoms: Array,
  filters: Object
})

/* ---------------- STATE ---------------- */
const localBoms = ref([])
const preview = ref({})

const productionUtilization = ref(90)
const planStartDate = ref(today())
const planEndDate = ref(null)

/* ---------------- INIT ---------------- */
onMounted(syncBoms)
watch(() => props.capBoms, syncBoms, { deep: true })

function today () {
  return new Date().toISOString().slice(0, 10)
}

function syncBoms () {
  
  localBoms.value = (props.capBoms || []).map(b => ({
    ...b,
    schedule_qty: Number(b.required_for_selected_qty || 0),
    machine: b.selected_workstation,
    mould: b.selected_mould || null,
    validation_error: null
  }))
  preview.value = {}
}

/* ---------------- CORE CALCULATION ---------------- */
const capacityData = computed(() => {
  return localBoms.value.map(b => {
    const cycle = Number(b.cycle_time || 0)
    const cavity = Math.max(1, Number(b.cavity || 1))

    const pcs_per_hour =
      cycle > 0 ? Math.floor(3600 / (cycle / cavity)) : 0

    const shift_hours = Number(b.shift_hours || 12)
    const pcs_per_shift =
      Math.floor(pcs_per_hour * shift_hours * (productionUtilization.value / 100))

    const required_shifts =
      pcs_per_shift > 0
        ? (b.schedule_qty / pcs_per_shift).toFixed(2)
        : 0

    const required_hours =
      pcs_per_hour > 0
        ? (b.schedule_qty / pcs_per_hour).toFixed(2)
        : 0

    return {
      ...b,
      pcs_per_hour,
      shift_hours,
      pcs_per_shift,
      required_shifts,
      required_hours,
      month_capacity: b.month_capacity_hours || 0
    }
  })
})

const totalRequiredHours = computed(() =>
  capacityData.value.reduce((a, b) => a + Number(b.required_hours), 0).toFixed(2)
)

const totalMonthlyCapacity = computed(() =>
  capacityData.value.reduce((a, b) => a + Number(b.month_capacity || 0), 0).toFixed(2)
)

/* ---------------- VALIDATION ---------------- */
async function validateAll () {
  const payload = {
    production_utilization: productionUtilization.value,
    plan_start_date: planStartDate.value,
    plan_end_date: planEndDate.value,
    lines: capacityData.value.map(b => ({
      bom_no: b.bom_no,
      fg_item: b.item_code,
      schedule_qty: b.schedule_qty,
      machine: b.machine,
      month: b.month,
      cycle_time: b.cycle_time,
      cavity: b.cavity
    }))
  }

  const res = await api.validateCapacity(payload)
   console.log("validate capacity data after api call responce :", res.data.message);
   
  capacityData.value.forEach(b => {
    const r = res.data.message.find(x => x.bom_no === b.bom_no)
    if (r && !r.ok) {
      b.validation_error = r.message
    }
  })
}

/* ---------------- PREVIEW ---------------- */
function computePreview () {
  preview.value = {}

  capacityData.value.forEach(b => {
    let remaining = b.schedule_qty
    let current = new Date(planStartDate.value)
    const end = planEndDate.value ? new Date(planEndDate.value) : null

    const rows = []
    let shift = 1

    while (remaining > 0) {
      if (end && current > end) break

      const qty = Math.min(b.pcs_per_shift, remaining)
      rows.push({
        date: current.toISOString().slice(0, 10),
        shift,
        qty
      })

      remaining -= qty
      shift++

      if (shift > 3) {
        shift = 1
        current.setDate(current.getDate() + 1)
      }
    }

    preview.value[b.bom_no] = rows
  })
}

/* ---------------- CREATE WOs ---------------- */
const canPlan = computed(() =>
  capacityData.value.length &&
  capacityData.value.every(b =>
    b.machine &&
    b.schedule_qty > 0 &&
    !b.validation_error
  )
)

async function planAndCreate () {
  computePreview()

  const payload = {
    production_utilization: productionUtilization.value,
    plan_start_date: planStartDate.value,
    plan_end_date: planEndDate.value,
    lines: capacityData.value.map(b => ({
      ...b,
      schedule: preview.value[b.bom_no]
    }))
  }

  const res = await api.createMSSPlan(payload)
  alert(`Created ${res.created_work_orders.length} Work Orders`)
  preview.value = {}
}
</script>
