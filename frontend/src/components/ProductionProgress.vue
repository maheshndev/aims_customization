<template>
  <div class="w-full">
    <div class="flex justify-between text-[11px] mb-1 text-gray-600">
      <span>{{ produced }} / {{ total }}</span>
      <span>{{ progress }}%</span>
    </div>

    <div class="h-2 bg-gray-200 rounded overflow-hidden">
      <div
        class="h-2 rounded transition-all"
        :class="progress >= 100 ? 'bg-green-500' : 'bg-blue-500'"
        :style="{ width: progress + '%' }"
      />
    </div>
  </div>
</template>

<script setup>
defineProps({
  total: {
    type: Number,
    default: 0
  },
  produced: {
    type: Number,
    default: 0
  },
  progress: {
    type: Number,
    default: 0
  }
})
</script>
