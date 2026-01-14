<template>
  <div class="bg-white p-2 sm:p-3 rounded-xl border border-gray-100 shadow-sm hover:shadow-md transition-shadow group">
    <div class="text-[9px] sm:text-[10px] uppercase tracking-wider text-gray-400 font-bold mb-0.5 sm:mb-1 group-hover:text-blue-500 transition-colors">
      {{ label }}
    </div>
    <div class="text-base sm:text-lg lg:text-xl font-bold text-gray-800 tabular-nums leading-tight">
      {{ value }}
    </div>
  </div>
</template>




<script setup>
defineProps({
  label: String,
  value: [String, Number]
})
</script>
