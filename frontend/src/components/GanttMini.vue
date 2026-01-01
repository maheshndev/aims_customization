<template>
  <div v-if="hasBars" class="relative h-10 bg-gray-100 rounded overflow-hidden">
    <div
      v-for="(bar, index) in normalizedBars"
      :key="index"
      class="absolute h-6 top-2 rounded text-[10px] text-white px-1 flex items-center whitespace-nowrap"
      :style="getBarStyle(bar)"
    >
      {{ bar.label }}
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

/**
 * Normalize & validate bars
 */
const normalizedBars = computed(() =>
  props.bars
    .filter(b => b?.start && b?.end)
    .map(b => ({
      label: b.label || "",
      start: new Date(b.start).getTime(),
      end: new Date(b.end).getTime()
    }))
    .filter(b => !isNaN(b.start) && !isNaN(b.end) && b.end > b.start)
)

const hasBars = computed(() => normalizedBars.value.length > 0)

const minTime = computed(() =>
  Math.min(...normalizedBars.value.map(b => b.start))
)

const maxTime = computed(() =>
  Math.max(...normalizedBars.value.map(b => b.end))
)

/**
 * Calculate bar style
 */
function getBarStyle(bar) {
  const total = maxTime.value - minTime.value
  if (total <= 0) return { display: "none" }

  const left = ((bar.start - minTime.value) / total) * 100
  const width = ((bar.end - bar.start) / total) * 100

  return {
    left: `${left}%`,
    width: `${Math.max(width, 3)}%`,
    backgroundColor: bar.label.startsWith("Job")
      ? "#6366f1"
      : "#10b981"
  }
}
</script>
