<template>
  <div class="p-6 bg-gray-50 min-h-screen font-sans space-y-6">

    <!-- Filters -->
    <SectionCard title="Filters">
      <Filters v-model="filters" @apply="onApplyFilters" />
    </SectionCard>

    <!-- Blanket Orders -->
    <SectionCard title="Blanket Orders">
      <BlanketOrders :filters="localFilters" v-model:selected="selected.blanketOrders"
        @bo-loaded="selected.items = $event" />
    </SectionCard>

    <!-- Blanket Order Items -->
    <SectionCard title="Items for Selected BO(s)">
      <BlanketOrderItems :selected-bo-names="selected.blanketOrders.map(b => b.name)"
        v-model:selected="selected.items" />
    </SectionCard>

    <!-- Sales Orders -->
    <SectionCard title="Sales Orders">
      <SalesOrders v-model:selected="selected.salesOrders" :items="filters.items" :customer="filters.customer"
        @so-loaded="state.salesOrders = $event" />
    </SectionCard>

    <!-- BOMs -->
    <SectionCard title="BOMs">
      <BOMList :sales-orders="selected.salesOrders" v-model:selected="selected.boms"
        @boms-loaded="state.boms = $event" />
    </SectionCard>

    <!-- Raw Materials -->
    <SectionCard title="Raw Materials">
      <RawMaterials :boms="selected.boms" v-model:selected="selected.rawMaterials"
        @raw-material-loaded="state.rawMaterialLoaded = $event" />
    </SectionCard>

    <SectionCard title="Capacity Planning">
      <CapacityPlanner :boms="selectedBOMObjects" :available-machine-hours="machineCapacity"
        @capacity-updated="handleCapacityUpdate" />
    </SectionCard>
    <BOMComparisonModal :open="state.showCompareModal" :boms="selectedBOMObjects" :raw-materials="rawMaterials"
      @close="state.showCompareModal = false" />

    <!-- Work Orders -->
    <SectionCard title="Work Orders">
      <WorkOrders :boList="selected.salesOrders" v-model:selected="selected.salesOrders"
        @wo-loaded="state.salesOrders = $event" />
    </SectionCard>

    <!-- Job Cards -->
    <SectionCard title="Job Cards">
      <JobCards :work-orders="selected.workOrders" v-model:selected="selected.jobCards"
        @js-loaded="state.jobCards = $event" />
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
  },

  setup() {
    // filters shared across components
    const filters = reactive({
      customer: "",
      month: "",
      year: "",
      blanket_order: "",
      search: "",
    });

    // All selected items
    const selected = reactive({
      blanketOrders: [],
      items: [],
      salesOrders: [],
      boms: [],
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
    };
    function handleCapacityUpdate(e) {
      state.capacity = e.capacity;
      state.capacitySummary = e.summary;
    }

    return { filters, selected, state, onApplyFilters };
  },
};
</script>
