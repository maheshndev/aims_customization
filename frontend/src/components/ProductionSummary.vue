<template>
  <div class="bg-white p-4 rounded shadow space-y-4">

    <table class="w-full border-collapse text-sm">
      <thead class="bg-gray-100">
        <tr>
          <th class="th">Item</th>
          <th class="th">Order Qty</th>
          <th class="th">Produced</th>
          <th class="th">Status</th>
          <th class="th">Timeline</th>
        </tr>
      </thead>

      <tbody>
        <tr v-for="r in rows" :key="r.item_code">
          <td class="td font-medium">{{ r.item_name }}</td>
          <td class="td">{{ r.order_qty }}</td>
          <td class="td text-green-600">{{ r.produced_qty }}</td>
          <td class="td">
            <StatusBadge :status="r.status" />
          </td>
          <td class="td">
            <GanttMini :bars="r.timeline" />
          </td>
        </tr>
      </tbody>
    </table>

  </div>
</template>
<script setup>
import { ref, onMounted } from "vue"
import { api } from "../services/api"
import StatusBadge from "./StatusBadge.vue"
import GanttMini from "./GanttMini.vue"

const props = defineProps({
  customer: { type: String, required: true }
})

const rows = ref([])

onMounted(async () => {
  const res = await api.getProductionControlDashboard(props.customer)
  rows.value = res.data
  console.log("Data Get From API: ",res.data);
  
})
</script>
