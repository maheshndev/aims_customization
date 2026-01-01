<template>
  <div class="bg-white p-3 rounded shadow-md text-center">
    <div class="text-xs text-gray-500">{{ label }}</div>
    <div class="text-xl font-semibold">{{ value }}</div>
  </div>
</template>

<script setup>
defineProps({
  label: String,
  value: [String, Number]
})
</script>
