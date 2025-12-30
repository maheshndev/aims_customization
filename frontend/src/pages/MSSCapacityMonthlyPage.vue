<template>
	<div class="min-h-screen bg-gray-50 p-6 space-y-6">
		<h2 class="text-xl font-semibold text-gray-800">Monthly Capacity Sheet</h2>

		<!-- Filters -->
		<SectionCard title="Filters">
			<CapacityFilters v-model="filters" @apply-filters="onApplyFilters" />
		</SectionCard>

		<!-- Machine Capacity -->
		<SectionCard title="Machine and Item Capacity Monthly Report">
			<MachineCapacityMonthly :filters="appliedFilters" v-model:selectedMachines="selectedMachines" />
		</SectionCard>

		<!-- Item Capacity -->
		<SectionCard title="Item Loading Monthly Report">
			<ItemsCapacityMonthly :filters="filters" :machines="selectedMachines" />
		</SectionCard>
	</div>
</template>

<script>
import { ref, reactive, toRefs } from "vue";

import SectionCard from "../components/layout/SectionCard.vue";
import CapacityFilters from "../components/CapacityFilters.vue";
import MachineCapacityMonthly from "../components/MachineCapacityMonthly.vue";
import ItemsCapacityMonthly from "../components/ItemsCapacityMonthly.vue";

export default {
	name: "MSSCapacityMonthlyPage",

	components: {
		SectionCard,
		CapacityFilters,
		MachineCapacityMonthly,
		ItemsCapacityMonthly,
	},

	setup() {
		// Editable filters (UI state)
		const filters = reactive({
			customer: "",
			month: "",
			year: "",
		});

		// Applied filters (used for API calls)
		const appliedFilters = reactive({ ...filters });

		// Selected machines from child
		const selectedMachines = ref([]);

		// Apply button handler
		const onApplyFilters = (newFilters) => {
			appliedFilters.customer = newFilters.customer;
			appliedFilters.month = newFilters.month;
			appliedFilters.year = newFilters.year;

			// Reset selected machines
			selectedMachines.value = [];
		};

		return {
			appliedFilters,
			selectedMachines,
			onApplyFilters,
			filters, // keep v-model reactive
		};
	},
};
</script>
