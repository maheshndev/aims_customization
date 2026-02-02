<template>
	<div class="p-6 bg-gray-50 min-h-screen font-sans space-y-6">
		<h2 class="p-2">Monthly Schedule Screen (MSS)</h2>
		<!-- Filters -->
		<SectionCard title="Filters">
			<Filters v-model="filters" @apply-filters="onApplyFilters" />
		</SectionCard>

		<!-- Pass filters to fetch list, use v-model:selected for selection -->
		<!-- <SectionCard title="Open Blanket Orders">
      <BlanketOrders :filters="filters" v-model:selected="selected.blanketOrders" />
    </SectionCard> -->

		<!-- Step 1: Select Blanket Order LINE ITEMS -->
		<SectionCard title="Open Blanket Order Line Items">
			<BlanketOrderItems
				:filters="filters"
				:selected-bo-names="selected.blanketOrders.map((b) => b.name)"
				v-model:selected="selected.items"
			/>
		</SectionCard>

		<!-- Step 2: Load Sales Orders ONLY from selected BO items -->
		<SectionCard title="Generated Sales Orders (Scheduled Orders)">
			<SalesOrders
				:filters="filters"
				:bo-items="selected.items"
				v-model:selected="selected.salesOrders"
			/>
		</SectionCard>

		<!-- Step 3: BOMs -->
		<SectionCard title="Bill Of Material">
			<BOMList
				ref="bomListRef"
				:sales-orders="selected.salesOrders"
				v-model:selected="selected.boms"
				@update:capBOMs="(val) => (selected.bomsObjects = val)"
			/>
		</SectionCard>

		<!-- Step 4: Raw Materials -->
		<SectionCard title="Raw Materials">
			<RawMaterials
				:boms="selected.boms"
				:filters="filters"
				v-model:selected="selected.rawMaterials"
				@raw-material-loaded="(val) => (state.allRawMaterials = val)"
			/>
		</SectionCard>

		<!-- Step 5: Capacity Planner -->
		<SectionCard title="Capacity Planner">
			<CapacityPlanner
				:boms="selected.boms"
				:cap-boms="selected.bomsObjects"
				:filters="filters"
				:raw-materials="state.allRawMaterials"
				:available-machine-hours="machineCapacity"
				@capacity-updated="handleCapacityUpdate"
				@refresh="onRefreshPlanning"
			/>
		</SectionCard>

		<!-- BOM Comparison Modal -->
		<!-- <BOMComparisonModal :open-compare="state.showCompareModal" :boms="selected.bomsObjects" :raw-materials="selected.rawMaterials"
      @close="state.showCompareModal = false" /> -->

		<!--Step 6: Work Orders -->
		<SectionCard title="Work Orders">
			<WorkOrders
				:sales-orders="selected.salesOrders"
				v-model:selected="selected.workOrders"
			/>
		</SectionCard>

		<!-- Step 7: Job Cards -->
		<SectionCard title="Job Cards">
			<JobCards :work-orders="selected.workOrders" v-model:selected="selected.jobCards" />
		</SectionCard>

		<!-- Step 8: Production Summary Section -->
		<SectionCard title="Production Summary">
			<ProductionSummary :filters="filters" :job-cards="selected.jobCards" />
		</SectionCard>
	</div>
</template>

<script>
import { reactive, ref } from "vue";
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
import BOMComparisonModal from "../components/BOMComparisonModal.vue";

export default {
	name: "MSSDashboard",
	components: {
		SectionCard,
		Filters,
		BlanketOrders,
		BlanketOrderItems,
		SalesOrders,
		BOMList,
		BOMComparisonModal,
		RawMaterials,
		WorkOrders,
		JobCards,
		ProductionSummary,
		CapacityPlanner,
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

		const bomListRef = ref(null);

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
			showCompareModal: false,
			allRawMaterials: [],
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

		function onRefreshPlanning() {
			if (bomListRef.value) {
				bomListRef.value.refreshBomList();
			}
		}

		return {
			filters,
			selected,
			state,
			onApplyFilters,
			handleCapacityUpdate,
			onRefreshPlanning,
			bomListRef,
		};
	},
};
</script>
