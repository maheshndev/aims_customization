<template>
    <div>
        <h2>Rescheduler Page</h2>
        <SectionCard title="Work Order Re-Scheduler">
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
