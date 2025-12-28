<template>
  <div v-if="bars?.length" class="relative h-10 bg-gray-100 rounded">
    <div
      v-for="(b, i) in bars"
      :key="i"
      class="absolute h-6 rounded text-xs text-white px-1 flex items-center"
      :style="barStyle(b)"
    >
      {{ b.label }}
    </div>
  </div>

  <div v-else class="text-xs text-gray-400 italic">
    No timeline
  </div>
</template>

<script setup>
import { computed } from "vue"

const props = defineProps({
  bars: {
    type: Array,
    default: () => []
  }
})

/* ---------------- TIME RANGE ---------------- */
const minTime = computed(() =>
  Math.min(...props.bars.map(b => +new Date(b.start)))
)

const maxTime = computed(() =>
  Math.max(...props.bars.map(b => +new Date(b.end)))
)

/* ---------------- STYLE CALC ---------------- */
function barStyle(b) {
  if (!b.start || !b.end || minTime.value === maxTime.value) {
    return { display: "none" }
  }

  const start = +new Date(b.start)
  const end = +new Date(b.end)

  const left = ((start - minTime.value) / (maxTime.value - minTime.value)) * 100
  const width = ((end - start) / (maxTime.value - minTime.value)) * 100

  return {
    left: `${left}%`,
    width: `${Math.max(width, 2)}%`,
    backgroundColor: b.label?.startsWith("Job") ? "#6366f1" : "#10b981"
  }
}
</script>
