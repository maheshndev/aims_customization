<template>
  <div class="p-6 bg-gray-50 min-h-screen font-sans space-y-6">
    <h2 class="p-2">MSS - Schedule Tool</h2>
    <!-- Filters -->
    <SectionCard title="Filters">
      <Filters v-model="filters" @apply-filters="onApplyFilters" />
    </SectionCard>

    <SectionCard title="Blanket Orders">
      <!-- Pass filters to fetch list, use v-model:selected for selection -->
      <BlanketOrders :filters="filters" v-model:selected="selected.blanketOrders" />
    </SectionCard>

    <SectionCard title="Items for Selected BO(s)">
      <!-- Fetch items in BlanketOrderItems based on selected BOs -->
      <BlanketOrderItems :selected-bo-names="selected.blanketOrders.map(b => b.name)"
        v-model:selected="selected.items" />
    </SectionCard>

    <!-- Sales Orders -->
    <SectionCard title="Sales Orders">
      <SalesOrders v-model:selected="selected.salesOrders" :items="filters.items" :customer="filters.customer" />
    </SectionCard>

    <!-- BOMs -->
    <SectionCard title="BOMs">
      <BOMList :sales-orders="selected.salesOrders" v-model:selected="selected.boms"
        @update:capBOMs="val => selected.bomsObjects = val" />

    </SectionCard>

    <!-- Raw Materials -->
    <SectionCard title="Raw Materials">
      <RawMaterials :boms="selected.boms" :filters="filters" v-model:selected="selected.rawMaterials" />
    </SectionCard>

    <SectionCard title="Capacity Planning">
      <CapacityPlanner :boms="selected.boms" :cap-boms="selected.bomsObjects" :filters="filters"
        :available-machine-hours="machineCapacity" @capacity-updated="handleCapacityUpdate" />

    </SectionCard>

    <BOMComparisonModal :open-compare="state.showCompareModal" :boms="selectedBOMObjects" :raw-materials="rawMaterials"
      @close="state.showCompareModal = false" />


    <!-- Work Orders -->
    <SectionCard title="Work Orders">
      <WorkOrders :sales-orders="selected.salesOrders" v-model:selected="selected.workOrders" />
    </SectionCard>

    <!-- Job Cards -->
    <SectionCard title="Job Cards">
      <JobCards :work-orders="selected.workOrders" v-model:selected="selected.jobCards" />
    </SectionCard>



    <!-- Production Summary -->
    <SectionCard title="Production Summary">
      <ProductionSummary :job-cards="selected.jobCards" :summary="state.productionSummary" />
    </SectionCard>

  </div>
</template>

<script>
import { reactive } from "vue";
import SectionCard from "../components/layout/SectionCard.vue";

// Components
import Filters from "../components/Filters.vue";
import BlanketOrders from "../components/BlanketOrders.vue";
import BlanketOrderItems from "../components/BlanketOrderItems.vue";
import SalesOrders from "../components/SalesOrders.vue";
import BOMList from "../components/BOMList.vue";
import RawMaterials from "../components/RawMaterials.vue";
import WorkOrders from "../components/WorkOrders.vue";
import JobCards from "../components/JobCards.vue";
import ProductionSummary from "../components/ProductionSummary.vue";
import CapacityPlanner from "../components/CapacityPlanner.vue";

export default {
  name: "MSSDashboard",
  components: {
    SectionCard,
    Filters,
    BlanketOrders,
    BlanketOrderItems,
    SalesOrders,
    BOMList,
    RawMaterials,
    WorkOrders,
    JobCards,
    ProductionSummary,
    CapacityPlanner
  },

  setup() {
    // filters shared across components
    const filters = reactive({
      customer: "",
      month: "",
      year: "",
    });

    // All selected items
    const selected = reactive({
      blanketOrders: [],
      items: [],
      salesOrders: [],
      boms: [],
      bomsObjects: [],
      rawMaterials: [],
      boList: [],
      workOrders: [],
      jobCards: [],
    });

    // Data loaded by each component
    const state = reactive({
      blanketOrders: [],
      blanketOrderItems: [],
      salesOrders: [],
      boms: [],
      capacity: {},
      rawMaterials: [],
      boList: [],
      workOrders: [],
      jobCards: [],
      productionSummary: {},
    });

    // When filters applied manually
    const onApplyFilters = () => {
      selected.blanketOrders = [];
      selected.items = [];
      selected.salesOrders = [];
      selected.boms = [];
      selected.rawMaterials = [];
      selected.workOrders = [];
      selected.jobCards = [];
    };
    function handleCapacityUpdate(e) {
      state.capacity = e.capacity;
    }

    return { filters, selected, state, onApplyFilters, handleCapacityUpdate };
  },
};
</script>
