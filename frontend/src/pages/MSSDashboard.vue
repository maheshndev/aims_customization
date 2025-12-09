<template>
  <div class="p-6 bg-gray-50 min-h-screen font-sans space-y-6">
    <!-- Filters -->
    <SectionCard title="Filters">
      <Filters :model-value="localFilters" :customers="state.customers" @update:modelValue="onFiltersUpdate"
        @apply-filters="onApplyFilters" />
    </SectionCard>

    <!-- Blanket Orders -->
    <SectionCard title="Blanket Orders">
      <BlanketOrders :filters="localFilters" v-model:selected="selected.blanketOrders"
        @items-loaded="selected.items = $event" />
    </SectionCard>

    <!-- Blanket Order Items -->
    <SectionCard title="Items for Selected BO(s)">
      <BlanketOrderItems :selected-bo-names="selected.blanketOrders.map(b => b.name)"
        v-model:selected="selected.items" />
    </SectionCard>


    <!-- Sales Orders (multi-select) -->
    <SectionCard title="Sales Orders">
      <SalesOrders :items="state.blanketOrderItems" :selected="selected.salesOrders"
        @update:selected="onSalesOrdersSelected" />
    </SectionCard>

    <!-- BOM List (multi-select) -->
    <SectionCard title="BOMs">
      <BOMList :sales-orders="state.salesOrders" :selected="selected.boms" @update:selected="onBOMsSelected" />
    </SectionCard>

    <!-- Raw Materials -->
    <SectionCard title="Raw Materials">
      <RawMaterials :boms="state.selectedBOMs" :selected="selected.rawMaterials"
        @update:selected="onRawMaterialsSelected" />
    </SectionCard>

    <!-- Work Orders -->
    <SectionCard title="Work Orders">
      <WorkOrders :raw-materials="state.rawMaterials" :selected="selected.workOrders"
        @update:selected="onWorkOrdersSelected" />
    </SectionCard>

    <!-- Job Cards -->
    <SectionCard title="Job Cards">
      <JobCards :work-orders="state.workOrders" :selected="selected.jobCards" @update:selected="onJobCardsSelected" />
    </SectionCard>

    <!-- Production Summary -->
    <SectionCard title="Production Summary">
      <ProductionSummary :job-cards="state.jobCards" :summary="state.productionSummary" />
    </SectionCard>
  </div>
</template>

<script>
import { reactive, ref, watch, onMounted } from "vue";
import { state } from "../store/index";
import { api } from "../services/api";

import Filters from "../components/Filters.vue";
import BlanketOrders from "../components/BlanketOrders.vue";
import BlanketOrderItems from "../components/BlanketOrderItems.vue";
import SalesOrders from "../components/SalesOrders.vue";
import BOMList from "../components/BOMList.vue";
import RawMaterials from "../components/RawMaterials.vue";
import WorkOrders from "../components/WorkOrders.vue";
import JobCards from "../components/JobCards.vue";
import ProductionSummary from "../components/ProductionSummary.vue";
import SectionCard from "../components/layout/SectionCard.vue";

export default {
  name: "MSSDashboard",
  components: {
    Filters,
    BlanketOrders,
    BlanketOrderItems,
    SalesOrders,
    BOMList,
    RawMaterials,
    WorkOrders,
    JobCards,
    ProductionSummary,
    SectionCard,
  },

  setup() {
    // Local reactive filters (keeps two-way with Filters component)
    const localFilters = reactive({
      customer: "",
      month: "",
      year: "",
      blanket_order: "",
      search: "",
    });

    // Fetch trigger toggled when Apply Filters pressed
    const fetchTrigger = ref(false);

    // Selected items at each stage (multi-select arrays)
    const selected = reactive({
      blanketOrders: [], // array of BO objects { name, customer_name, ... }
      items: [], // array of item objects
      salesOrders: [],
      boms: [],
      rawMaterials: [],
      workOrders: [],
      jobCards: [],
    });

    // Initialization: load customers + optional initial blanket orders
    const fetchCustomers = async () => {
      try {
        const res = await api.getCustomers();
        state.customers = res.data.message || [];
      } catch (e) {
        console.error("getCustomers failed", e);
        state.customers = [];
      }
    };

    // Blanket orders are fetched by BlanketOrders child (it calls API based on filters).
    // But we still expose this method in case other parts need to call.
    const fetchBlanketOrdersDirect = async () => {
      try {
        const res = await api.getBlanketOrders({
          customer: localFilters.customer,
          month: localFilters.month,
          year: localFilters.year,
          blanket_order: localFilters.blanket_order,
        });
        state.blanketOrders = res.data.message || [];
      } catch (e) {
        console.error("fetchBlanketOrdersDirect failed", e);
        state.blanketOrders = [];
      }
    };

    // Handler: Filters updated (two-way)
    const onFiltersUpdate = (newFilters) => {
      Object.assign(localFilters, newFilters);
      // When filters change, BlanketOrders child will auto-fetch (it watches the filters prop)
    };

    // Handler: Apply button pressed in Filters
    // toggles fetchTrigger so BlanketOrders sees the change and fetches
    const onApplyFilters = () => {
      fetchTrigger.value = true;
      // reset quickly so the child can trigger on rising edge
      setTimeout(() => {
        fetchTrigger.value = false;
      }, 10);
    };

    // BlanketOrders -> emits loaded list
    const onBlanketOrdersLoaded = (list) => {
      state.blanketOrders = list || [];
      // clear downstream selections when new BO list loads
      selected.items = [];
      selected.salesOrders = [];
      selected.boms = [];
      selected.rawMaterials = [];
      selected.workOrders = [];
      selected.jobCards = [];

      // Optionally auto-select first if you want
      // selected.blanketOrders = list.length ? [list[0]] : [];
    };

    // When user selects/unselects BOs (array), update state and fetch items for those BOs
    const onBlanketOrdersSelected = async (selectedBOs) => {
      selected.blanketOrders = selectedBOs || [];
      const boNames = selected.blanketOrders.map((b) => b.name);
      if (boNames.length === 0) {
        state.blanketOrderItems = [];
        return;
      }

      // fetch items for selected BOs
      try {
        const res = await api.getBlanketOrderItems(boNames);
        // assume API returns array of items (flattened)
        state.blanketOrderItems = res.data || [];
      } catch (e) {
        console.error("getBlanketOrderItems failed", e);
        state.blanketOrderItems = [];
      }
    };

    // Items selected -> fetch sales orders for those items
    const selectedOrders = async (itemsArray) => {
      selected.items = itemsArray || [];
      if (!selected.items.length) {
        state.salesOrders = [];
        return;
      }
      const itemCodes = selected.items.map((i) => i.item_code || i.code || i.name);
      try {
        const res = await api.getSalesOrders(itemCodes);
        state.salesOrders = res.data || [];
      } catch (e) {
        console.error("getSalesOrders failed", e);
        state.salesOrders = [];
      }
    };

    // Sales orders selected -> fetch BOMs for items (or sales orders)
    const onSalesOrdersSelected = async (salesOrdersArray) => {
      selected.salesOrders = salesOrdersArray || [];
      if (!selected.salesOrders.length) {
        state.selectedBOMs = [];
        return;
      }
      try {
        // assuming API accepts sales order ids to derive boms
        const res = await api.getBOMsForItems(selected.salesOrders.map(s => s.name));
        state.selectedBOMs = res.data || [];
      } catch (e) {
        console.error("getBOMsForItems failed", e);
        state.selectedBOMs = [];
      }
    };

    // BOMs selected -> fetch raw materials
    const onBOMsSelected = async (bomsArray) => {
      selected.boms = bomsArray || [];
      if (!selected.boms.length) {
        state.rawMaterials = [];
        return;
      }
      try {
        const res = await api.getRawMaterialsForBOMs(selected.boms.map(b => b.name));
        state.rawMaterials = res.data || [];
      } catch (e) {
        console.error("getRawMaterialsForBOMs failed", e);
        state.rawMaterials = [];
      }
    };

    // Raw materials selected -> create / fetch work orders
    const onRawMaterialsSelected = async (rawArray) => {
      selected.rawMaterials = rawArray || [];
      if (!selected.rawMaterials.length) {
        state.workOrders = [];
        return;
      }
      try {
        // Example: fetch or compute work orders that need these raw materials
        const res = await api.getWorkOrders(selected.rawMaterials.map(r => r.item_code || r.name));
        state.workOrders = res.data || [];
      } catch (e) {
        console.error("getWorkOrders failed", e);
        state.workOrders = [];
      }
    };

    // Work orders selected -> fetch job cards
    const onWorkOrdersSelected = async (workOrdersArray) => {
      selected.workOrders = workOrdersArray || [];
      if (!selected.workOrders.length) {
        state.jobCards = [];
        return;
      }
      try {
        const res = await api.getJobCards(selected.workOrders.map(w => w.name));
        state.jobCards = res.data || [];
      } catch (e) {
        console.error("getJobCards failed", e);
        state.jobCards = [];
      }
    };

    // Job cards selected -> fetch/update production summary
    const onJobCardsSelected = async (jobCardsArray) => {
      selected.jobCards = jobCardsArray || [];
      try {
        const res = await api.getProductionSummary(selected.jobCards.map(j => j.name));
        state.productionSummary = res.data || {};
      } catch (e) {
        console.error("getProductionSummary failed", e);
        state.productionSummary = {};
      }
    };

    // mount lifecycle
    onMounted(() => {
      fetchCustomers();

      // optional initial fetch: uncomment if you want initial BO list
      // fetchBlanketOrdersDirect();
    });

    // expose to template
    return {
      state,
      localFilters,
      fetchTrigger,
      fetchBlanketOrders: fetchBlanketOrdersDirect,
      selected,
      onFiltersUpdate,
      onApplyFilters,
      onBlanketOrdersLoaded,
      onBlanketOrdersSelected,
      selectedOrders,
      onSalesOrdersSelected,
      onBOMsSelected,
      onRawMaterialsSelected,
      onWorkOrdersSelected,
      onJobCardsSelected,
    };
  },
};
</script>

<style scoped>
body {
  font-family: "Inter", sans-serif;
}
</style>
