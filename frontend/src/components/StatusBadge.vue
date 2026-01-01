<template>
  <span :class="badgeClass">
    {{ status || "Unknown" }}
  </span>
</template>

<script setup>
import { computed } from "vue"

const props = defineProps({
  status: {
    type: String,
    default: ""
  }
})

const badgeClass = computed(() => {
  const base = "px-2 py-1 rounded text-xs font-medium inline-block"

  switch (props.status) {
    case "Production Completed":
      return `${base} bg-green-100 text-green-700`
    case "In Production":
      return `${base} bg-blue-100 text-blue-700`
    case "Planned":
      return `${base} bg-yellow-100 text-yellow-700`
    default:
      return `${base} bg-gray-100 text-gray-600`
  }
})
</script>
