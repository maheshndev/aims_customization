<template>
  <div class="p-4 bg-white rounded shadow space-y-4">

    <!-- HEADER ACTIONS -->
    <div class="flex flex-wrap items-end justify-between gap-4">
      <div class="flex gap-2">
        <button class="px-3 py-1 rounded bg-blue-100 hover:bg-blue-200" @click="validateCapacity"
          :disabled="!selectedRows.length">
          Validate Capacity
        </button>

        <button class="px-3 py-1 rounded bg-indigo-100 hover:bg-indigo-200" @click="loadPreview"
          :disabled="!selectedRows.length">
          Preview Schedule
        </button>

        <button class="px-3 py-1 rounded bg-green-200 hover:bg-green-300" @click="createWorkOrders"
          :disabled="!selectedRows.length">
          Plan & Create WOs
        </button>
      </div>

      <div class="flex gap-3 text-sm">
        <div>
          <label class="block text-xs text-gray-500">Utilization %</label>
          <input type="number" v-model.number="utilization" min="1" max="100" class="border rounded px-2 py-1 w-20" />
        </div>

        <div>
          <label class="block text-xs text-gray-500">Plan Start</label>
          <input type="date" v-model="planStart" class="border rounded px-2 py-1" />
        </div>

        <div>
          <label class="block text-xs text-gray-500">Plan End</label>
          <input type="date" v-model="planEnd" class="border rounded px-2 py-1" />
        </div>
      </div>
    </div>

    <!-- EMPTY -->
    <div v-if="!rows.length" class="text-gray-400 text-sm">
      No items selected
    </div>

    <!-- TABLE -->
    <div v-else class="overflow-auto">
      <table class="min-w-[1500px] w-full border text-sm">
        <thead class="bg-gray-100 text-xs uppercase">
          <tr>
            <th class="border p-2 text-center">
              <input type="checkbox" v-model="selectAll" @change="toggleAll" />
            </th>
            <th class="border p-2">#</th>
            <th class="border p-2">Customer</th>
            <th class="border p-2">Sales Order</th>
            <th class="border p-2">Item</th>
            <th class="border p-2">BOM</th>
            <th class="border p-2">Machine</th>
            <th class="border p-2">Mould</th>
            <th class="border p-2 text-right">Qty</th>
            <th class="border p-2 text-right">Cycle</th>
            <th class="border p-2 text-right">Cavity</th>
            <th class="border p-2 text-right">Pcs/Hr</th>
            <th class="border p-2 text-right">Req Hrs</th>
            <th class="border p-2">Status</th>
            <th class="border p-2 text-center">Preview</th>
          </tr>
        </thead>

        <tbody>
          <template v-for="(r, i) in rows" :key="r.rowKey">
            <tr class="hover:bg-gray-50">
              <td class="border p-2 text-center">
                <input type="checkbox" :value="r.rowKey" v-model="selectedKeys" />
              </td>
              <td class="border p-2">{{ i + 1 }}</td>
              <td class="border p-2 font-medium">{{ r.customer }}</td>
              <td class="border p-2">{{ r.sales_order }}</td>
              <td class="border p-2">{{ r.item_code }}</td>
              <td class="border p-2">{{ r.bom_no }}</td>
              <td class="border p-2">{{ r.machine }}</td>
              <td class="border p-2">{{ r.mould || "—" }}</td>
              <td class="border p-2 text-right">{{ r.schedule_qty }}</td>
              <td class="border p-2 text-right">{{ r.cycle_time }}</td>
              <td class="border p-2 text-right">{{ r.cavity }}</td>
              <td class="border p-2 text-right">{{ r.pcs_per_hour }}</td>
              <td class="border p-2 text-right">{{ r.required_hours }}</td>

              <!-- STATUS -->
              <td class="border p-2">
                <span v-if="r.validation_error" class="text-red-600 text-xs">
                  {{ r.validation_error }}
                </span>
                <span v-else class="text-green-600 text-xs font-medium">
                  OK
                </span>
              </td>

              <!-- PREVIEW -->
              <td class="border p-2 text-center">
                <button class="px-2 py-0.5 text-xs border rounded bg-gray-50" @click="togglePreview(r)">
                  {{ preview[r.bom_no] ? "Hide" : "View" }}
                </button>
              </td>
            </tr>

            <!-- PREVIEW ROW -->
            <tr v-if="preview[r.bom_no]">
              <td colspan="15" class="bg-gray-50 p-3">
                <div class="flex flex-wrap gap-2">
                  <div v-for="(p, idx) in preview[r.bom_no]" :key="idx"
                    class="px-2 py-1 border rounded text-xs bg-white">
                    {{ p.date }} | Shift {{ p.shift }} → {{ p.qty }}
                  </div>
                </div>
              </td>
            </tr>
          </template>
        </tbody>
      </table>
    </div>

    <!-- SUMMARY -->
    <div class="text-sm flex gap-6">
      <div>
        Required Hours:
        <b>{{ totalRequiredHours }}</b>
      </div>
      <div>
        Selected Rows:
        <b>{{ selectedRows.length }}</b>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from "vue"
import { api } from "../services/api"

/* ---------------- PROPS ---------------- */
const props = defineProps({
  capBoms: { type: Array, default: () => [] }
})

/* ---------------- STATE ---------------- */
const rows = ref([])
const preview = ref({})
const selectedKeys = ref([])
const selectAll = ref(false)

const utilization = ref(90)
const planStart = ref(today())
const planEnd = ref(null)

/* ---------------- INIT ---------------- */
onMounted(sync)
watch(() => props.capBoms, sync, { deep: true })

function today() {
  return new Date().toISOString().slice(0, 10)
}

function sync() {
  rows.value = props.capBoms.map((b, i) => ({
    ...b,
    rowKey: `${b.bom_no}_${b.sales_order}_${i}`,
    schedule_qty: Number(b.required_for_selected_qty || 0),
    machine: b.selected_workstation,
    mould: b.selected_mould || null,
    validation_error: null
  }))
  preview.value = {}
  selectedKeys.value = []
}

/* ---------------- COMPUTED ---------------- */
const selectedRows = computed(() =>
  rows.value.filter(r => selectedKeys.value.includes(r.rowKey))
)

const totalRequiredHours = computed(() =>
  selectedRows.value
    .reduce((a, b) => a + Number(b.required_hours || 0), 0)
    .toFixed(2)
)

/* ---------------- SELECTION ---------------- */
function toggleAll() {
  selectedKeys.value = selectAll.value
    ? rows.value.map(r => r.rowKey)
    : []
}

/* ---------------- VALIDATE ---------------- */
async function validateCapacity() {
  const payload = {
    production_utilization: utilization.value,
    plan_start_date: planStart.value,
    plan_end_date: planEnd.value,
    lines: selectedRows.value.map(r => ({
      item_code: r.item_code,
      bom_no: r.bom_no,
      schedule_qty: r.schedule_qty,
      machine: r.machine
    }))
  }

  const res = await api.validateCapacity(payload)
  const result = res.data.message || []

  rows.value.forEach(r => {
    const v = result.find(
      x => x.bom_no === r.bom_no && x.item === r.item_code
    )

    if (!v) return

    /* ✅ refresh row fields */
    r.required_hours = v.required_hours
    r.available_hours = v.available_hours
    r.capacity_gap = v.capacity_gap
    r.validation_error = v.ok ? null : "Insufficient capacity"
  })
}


/* ---------------- PREVIEW ---------------- */
async function loadPreview() {
  preview.value = {}

  const payload = {
    production_utilization: utilization.value,
    plan_start_date: planStart.value,
    plan_end_date: planEnd.value,
    lines: selectedRows.value.map(r => ({
      item_code: r.item_code,
      schedule_qty: r.schedule_qty,
      machine: r.machine
    }))
  }

  const res = await api.getCapacityPlan(payload)
const data = res.data.message || []

data.forEach(p => {
  preview.value[p.item] = p.preview
})

}

async function togglePreview(row) {
  if (preview.value[row.bom_no]) {
    delete preview.value[row.bom_no]
    return
  }

  await loadPreview()
}

/* ---------------- CREATE ---------------- */
async function createWorkOrders() {
  const payload = {
    production_utilization: utilization.value,
    plan_start_date: planStart.value,
    plan_end_date: planEnd.value,
    lines: selectedRows.value
  }

  const res = await api.createMSSPlan(payload)
  alert(`Created ${res.data.created_work_orders.length} Work Orders`)
  preview.value = {}
}
</script>
