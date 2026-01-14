<template>
	<div class="min-h-screen bg-gray-50 p-6 space-y-6">
		<h2 class="text-xl font-semibold text-gray-800">Monthly Capacity Sheet</h2>

		<!-- Filters -->
		<SectionCard title="Filters">
			<CapacityFilters v-model="filters" @apply-filters="onApplyFilters" />
		</SectionCard>

		<!-- Machine Capacity -->
		<SectionCard title="Available Machines">
			<MachineCapacityMonthly :filters="filters" v-model:selected="selected.selectedMachines" />
		</SectionCard>

		<!-- Item Capacity -->
		<SectionCard title="Items Monthly Capacity Report ">
			<ItemsCapacityMonthly :filters="filters" :selected-machines="selected.selectedMachines" />
		</SectionCard>
	</div>
</template>

<script>
import { reactive } from "vue";

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
		const today = new Date();
		const filters = reactive({
			customer: "",
			month: String(today.getMonth() + 1).padStart(2, "0"),
			year: String(today.getFullYear()),
		});

		const selected = reactive({
			selectedMachines: []
		});

		const state = reactive({
			selectedMachines: []
		});

		const onApplyFilters = () => {
			selected.selectedMachines = [];
		};

		return { filters, selected, state, onApplyFilters };
	},
};
</script>
