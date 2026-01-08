<template>
    <div class="p-6 bg-gray-50 min-h-screen font-sans space-y-6">
        <h2>Rescheduler Screen</h2>
        <SectionCard title="">
            <WorkOrderRescheduler />
        </SectionCard>
    </div>
</template>

<script setup>
    
import { reactive } from "vue";
import WorkOrderRescheduler from "../components/WorkOrderRescheduler.vue";
import SectionCard from "../components/layout/SectionCard.vue";
</script>

<style lang="scss" scoped></style>
