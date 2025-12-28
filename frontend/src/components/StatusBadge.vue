<template>
  <span :class="cls">{{ status }}</span>
</template>

<script setup>
import { computed } from "vue"

const props = defineProps({ status: String })

const cls = computed(() => ({
  "px-2 py-1 rounded text-xs": true,
  "bg-green-100 text-green-700": props.status.includes("Completed"),
  "bg-blue-100 text-blue-700": props.status === "In Production",
  "bg-yellow-100 text-yellow-700": props.status === "Planned",
  "bg-red-100 text-red-700": props.status.includes("Missing")
}))
</script>
