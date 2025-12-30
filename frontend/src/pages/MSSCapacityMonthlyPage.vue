<template>
  <div class="min-h-screen bg-gray-50 p-6 space-y-6">
    <!-- Page Title -->
    <h2 class="text-xl font-semibold text-gray-800">
      Monthly Capacity Sheet
    </h2>

    <!-- Filters -->
    <SectionCard title="Filters">
      <CapacityFilters v-model="filters" />
    </SectionCard>

    <!-- Machine Capacity -->
    <SectionCard title="Machine and Item Capacity Monthly Report">
      <MachineCapacityMonthly :filters="filters" />
    </SectionCard>

    <!-- Item Capacity -->
    <SectionCard title="Item Loading Monthly Report">
      <ItemsCapacityMonthly :filters="filters" />
    </SectionCard>
  </div>
</template>

<script setup>
import { ref } from "vue";

import SectionCard from "../components/layout/SectionCard.vue";
import CapacityFilters from "../components/CapacityFilters.vue";
import MachineCapacityMonthly from "../components/MachineCapacityMonthly.vue";
import ItemsCapacityMonthly from "../components/ItemsCapacityMonthly.vue";

/**
 * Reactive filters state
 * Passed down to child components
 */
const filters = ref({
  month: "",
  year: "",
  customer: ""
});
</script>
