<template>
	<div class="p-4 shadow-md border border-gray-200 rounded-lg relative">

		<!-- Filter Row (Month, Year, Customer) -->
		<div class="flex flex-wrap gap-3">

			<!-- Month -->
			<div class="relative flex-1  m-1">
				<label class="filter-label mb-1 block">Month</label>
				<div class="relative">
					<select v-model="localFilters.month" class="filter-input pr-5 p-1 rounded-sm">
						<option value="">Select Month</option>
						<option v-for="m in monthOptions" :key="m.value" :value="m.value">{{ m.label }}</option>
					</select>
					<span v-if="localFilters.month" @click="clearMonth"
						class="absolute right-2 top-1/2 -translate-y-1/2 cursor-pointer text-gray-400 hover:text-gray-700">
						✕
					</span>
				</div>
			</div>

			<!-- Year -->
			<div class="relative flex-1 m-1">
				<label class="filter-label mb-1 block">Year</label>
				<div class="relative">
					<select v-model="localFilters.year" class="filter-input pr-5 p-1 rounded-sm">
						<option value="">Select Year</option>
						<option v-for="y in yearOptions" :key="y" :value="y">{{ y }}</option>
					</select>
					<span v-if="localFilters.year" @click="clearYear"
						class="absolute right-2 top-1/2 -translate-y-1/2 cursor-pointer text-gray-400 hover:text-gray-700">
						✕
					</span>
				</div>
			</div>

			<!-- Customer -->
			<div class="relative flex-[2] m-1">
				<label class="filter-label mb-1 block">Customer</label>
				<div class="relative ">
					<input type="text" v-model="searchCustomer" placeholder="Search customer..."
						class="filter-input w-full pr-5  p-1 rounded-sm" @focus="dropdownOpen = true"
						@input="dropdownOpen = true" @keydown.down.prevent="highlightNext"
						@keydown.up.prevent="highlightPrev" @keydown.enter.prevent="selectHighlighted"
						@keydown.esc.prevent="dropdownOpen = false"  />
					<!-- Clear icon -->
					<span v-if="searchCustomer" @click="clearCustomer"
						class="absolute right-2 top-1/2 -translate-y-1/2 cursor-pointer text-gray-400 hover:text-gray-700">
						✕
					</span>
				</div>

				<!-- Dropdown -->
				<ul v-if="dropdownOpen"
					class="absolute left-0 w-full border rounded-lg shadow-lg mt-1 z-15 max-h-40 overflow-y-auto bg-white animate-fadeIn">
					<li v-for="(c, index) in filteredCustomers" :key="c.value" @click="selectCustomer(c)"
						@mouseenter="highlightedIndex = index" :class="[
							'px-3 py-1 text-sm cursor-pointer rounded-md transition',
							highlightedIndex === index ? 'bg-blue-100 text-blue-700' : 'hover:bg-gray-100'
						]" >
						{{ c.label }}
					</li>
					<li v-if="filteredCustomers.length === 0" class="px-3 py-2 text-sm text-gray-500">
						No results found
					</li>
				</ul>
			</div>

		</div>

		<!-- Action Buttons -->
		<div class="flex justify-start gap-2 mt-4">
			<button class="bg-gray-200 hover:bg-gray-200 border border-gray-300 text-black font-semibold py-1 px-3 rounded min-w-[200px] m-1"
				@click="resetFilters" tooltip="Hover for more!">
				Reset All
			</button>

			<button class="bg-blue-100 hover:bg-blue-200 border border-gray-300 text-black font-semibold py-1 px-3 rounded min-w-[200px] m-1"
				@click="onApplyFilters">
				Apply Filters
			</button>
		</div>

	</div>
</template>

<script>
import { api } from "../services/api";

export default {
	name: "Filters",

	props: {
		modelValue: { type: Object, required: true },
	},

	emits: ["update:modelValue", "apply-filters"],

	data() {
		return {
			dropdownOpen: false,
			searchCustomer: "",
			customers: [],
			highlightedIndex: -1,
			localFilters: { ...this.modelValue },
			monthOptions: [
				{ value: "01", label: "January" },
				{ value: "02", label: "February" },
				{ value: "03", label: "March" },
				{ value: "04", label: "April" },
				{ value: "05", label: "May" },
				{ value: "06", label: "June" },
				{ value: "07", label: "July" },
				{ value: "08", label: "August" },
				{ value: "09", label: "September" },
				{ value: "10", label: "October" },
				{ value: "11", label: "November" },
				{ value: "12", label: "December" },
			],
		};
	},

	computed: {
		yearOptions() {
			const current = new Date().getFullYear();
			return Array.from({ length: 6 }, (_, i) => current - 2 + i);
		},
		filteredCustomers() {
			if (!this.searchCustomer) return this.customers;
			return this.customers.filter((c) =>
				c.label.toLowerCase().includes(this.searchCustomer.toLowerCase())
			);
		},
	},

	watch: {
		modelValue(newVal) {
			this.localFilters = { ...newVal };
		},
		localFilters: {
			deep: true,
			handler(val) {
				this.$emit("update:modelValue", val);
			},
		},
	},

	methods: {
		async fetchCustomers() {
			const res = await api.getCustomers();
			this.customers = res.data.message.map((c) => ({
				value: c.name,
				label: c.customer_name || c.name,
			}));
		},

		selectCustomer(customer) {
			this.localFilters.customer = customer.value;
			this.searchCustomer = customer.value;
			this.dropdownOpen = false;
		},

		highlightNext() {
			if (this.highlightedIndex < this.filteredCustomers.length - 1) this.highlightedIndex++;
		},
		highlightPrev() {
			if (this.highlightedIndex > 0) this.highlightedIndex--;
		},
		selectHighlighted() {
			if (this.highlightedIndex >= 0)
				this.selectCustomer(this.filteredCustomers[this.highlightedIndex]);
		},

		clearCustomer() {
			this.searchCustomer = "";
			this.localFilters.customer = "";
			this.highlightedIndex = -1;
		},
		clearMonth() {
			this.localFilters.month = "";
		},
		clearYear() {
			this.localFilters.year = "";
		},

		resetFilters() {
			this.clearCustomer();
			this.clearMonth();
			this.clearYear();
		},

		onApplyFilters() {
			const filtersToApply = { ...this.localFilters };
			this.$emit("apply-filters", filtersToApply);
		},

		outsideClick(e) {
			if (!this.$el.contains(e.target)) {
				this.dropdownOpen = false;
			}
		},
	},

	mounted() {
		this.fetchCustomers();
		document.addEventListener("click", this.outsideClick);
	},

	beforeUnmount() {
		document.removeEventListener("click", this.outsideClick);
	},
};
</script>

<style>
@keyframes fadeIn {
	from {
		opacity: 0;
		transform: translateY(-4px);
	}

	to {
		opacity: 1;
		transform: translateY(0);
	}
}

.animate-fadeIn {
	animation: fadeIn 0.15s ease-out;
}

.filter-label {
	font-weight: 700;
	width: 350px;
}

.filter-input {
	width: 350px;
	padding: 10px;
	border: 1px solid #d1d5db;
	border-radius: 0.375rem;
}
</style>
