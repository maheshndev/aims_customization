<template>
	<div class="p-4 shadow-sm border border-gray-200 rounded-lg bg-white relative">
		<p>Select Year, Month And Customer For Production Planning</p>

		<div class="flex flex-wrap gap-5">
			
			<div class="relative flex-1 min-w-[100px] max-w-[210px] mx-1">
				<label class="block text-sm font-medium text-gray-700 mb-1">Year (Optional)</label>
				<div class="relative">
					<select v-model="localFilters.year"
						class="w-full h-9 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 pr-8 pl-2 text-sm">
						<option value="">Select Year (Optional)</option>
						<option v-for="y in yearOptions" :key="y" :value="y">{{ y }}</option>
					</select>
					<span v-if="localFilters.year" @click="clearYear"
						class="absolute px-2 top-1/2 transform -translate-y-1/2 cursor-pointer text-gray-400 hover:text-gray-700 text-base leading-none">
						<b>✕</b>
					</span>
				</div>
			</div>
			<div class="relative flex-1 min-w-[100px] max-w-[210px] mx-1">
				<label class="block text-sm font-medium text-gray-700 mb-1">Month (Optional)</label>
				<div class="relative">
					<select v-model="localFilters.month"
						class="w-full h-9 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 pr-8 pl-2 text-sm">
						<option value="">Select Month (Optional)</option>
						<option v-for="m in monthOptions" :key="m.value" :value="m.value">
							{{ m.label }}
						</option>
					</select>
					<span v-if="localFilters.month" @click="clearMonth"
						class="absolute px-1 top-1/2 transform -translate-y-1/2 cursor-pointer text-gray-400 hover:text-gray-700 text-base leading-none">
						<b>✕</b>
					</span>
				</div>
			</div>

			<div class="relative flex-3 min-w-[100px] max-w-[350px] mx-1">
				<label class="block text-sm font-medium text-gray-700 mb-1">Customer <span class="text-red-700"> * Important</span></label>
				<div class="relative">
					<input type="text" v-model="searchCustomerText" placeholder="Search customer..."
						class="w-full h-9 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 pr-8 pl-2 text-sm"
						@focus="handleCustomerFocus" @input="handleCustomerInput" @keydown.down.prevent="highlightNext"
						@keydown.up.prevent="highlightPrev" @keydown.enter.prevent="selectHighlighted"
						@keydown.esc.prevent="dropdownOpen = false" />
					<span v-if="localFilters.customer || searchCustomerText" @click="clearCustomer"
						class="absolute px-2 top-1/2 transform -translate-y-1/2 cursor-pointer text-gray-400 hover:text-gray-700 text-base leading-none">
						<b>✕</b>
					</span>
				</div>

				<ul v-if="dropdownOpen"
					class="absolute left-0 w-full border border-gray-300 rounded-md shadow-lg mt-1 z-10 max-h-60 overflow-y-auto bg-white">
					<li v-if="customerSearchLoading" class="px-3 py-2 text-sm text-gray-500 flex items-center">
						<svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-blue-500" xmlns="http://www.w3.org/2000/svg"
							fill="none" viewBox="0 0 24 24">
							<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4">
							</circle>
							<path class="opacity-75" fill="currentColor"
								d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z">
							</path>
						</svg>
						Searching...
					</li>

					<li v-for="(c, index) in customers" :key="c.value" @click="selectCustomer(c)"
						@mouseenter="highlightedIndex = index" :class="[
							'px-3 py-2 text-sm cursor-pointer transition border-b last:border-b-0',
							highlightedIndex === index
								? 'bg-blue-100 text-blue-700'
								: 'hover:bg-gray-50',
						]">
						{{ c.label }}
						<span v-if="c.value !== c.label" class="text-xs text-gray-400 ml-2">({{ c.value }})</span>
					</li>
					<li v-if="!customerSearchLoading && customers.length === 0" class="px-3 py-2 text-sm text-gray-500">
						No customers found matching "{{ searchCustomerText }}"
					</li>
				</ul>
			</div>
		</div>
		
		<div class="flex justify-start gap-3 mt-3 pt-2">
			<button
				class="flex items-center justify-center bg-gray-50 hover:bg-gray-100 border border-gray-300 text-gray-700 font-semibold py-1.5 px-4 rounded shadow-sm transition duration-150"
				@click="resetFilters">
				<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24"
					stroke="currentColor" stroke-width="2">
					<path stroke-linecap="round" stroke-linejoin="round"
						d="M4 4v5h.582m15.356 2A8.001 8.001 0 004 12a7.961 7.961 0 00-1.565 3.59M18 20v-5h.582m-15.356-2A8.001 8.001 0 0120 12a7.961 7.961 0 011.565-3.59" />
				</svg>
				Reset All
			</button>

			<button
				class="flex items-center justify-center bg-blue-600 hover:bg-blue-700 text-white font-semibold py-1.5 px-4 rounded shadow-md transition duration-150"
				@click="onApplyFilters">
				<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24"
					stroke="currentColor" stroke-width="2">
					<path stroke-linecap="round" stroke-linejoin="round"
						d="M9 12l2 2 4-4m5.618-4.111a.75.75 0 01-.197 1.055l-4.522 3.86a.75.75 0 01-.894 0l-4.522-3.86a.75.75 0 01-.197-1.055l3.86-4.522a.75.75 0 011.055-.197l4.522 3.86a.75.75 0 01.197 1.055z" />
				</svg>
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
			searchCustomerText: "", 
			customers: [], 
			highlightedIndex: -1,
			localFilters: { ...this.modelValue },
			customerSearchLoading: false,
			debouncedFetchCustomers: null,

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
	},

	watch: {
		modelValue(newVal) {
			this.localFilters = { ...newVal };
			if (newVal.customer && newVal.customer !== this.localFilters.customer) {
				this.setInitialCustomerDisplay(newVal.customer);
			} else if (!newVal.customer) {
				this.searchCustomerText = "";
			}
		},
		localFilters: {
			deep: true,
			handler(val) {
				this.$emit("update:modelValue", val);
			},
		},
		searchCustomerText(newVal) {
			if (!newVal) {
				this.clearCustomerFilterOnly();
			}
		},
	},

	methods: {
		debounce(func, delay) {
			let timeout;
			return function (...args) {
				clearTimeout(timeout);
				timeout = setTimeout(() => {
					func.apply(this, args);
				}, delay);
			};
		},

		async fetchCustomers(searchText = "") {
			this.customerSearchLoading = true;
			try {
				const res = await api.getCustomers(searchText);
				this.customers = res.data.message.map((c) => ({
					value: c.name,
					label: c.customer_name || c.name,
				}));
			} catch (error) {
				console.error("Failed to fetch customers:", error);
				this.customers = [];
			} finally {
				this.customerSearchLoading = false;
			}
		},

		async handleCustomerFocus() {
			this.dropdownOpen = true;

			if (!this.searchCustomerText && this.customers.length === 0) {
				await this.fetchCustomers("");
			}
		},

		handleCustomerInput() {
			this.localFilters.customer = "";
			this.debouncedFetchCustomers(this.searchCustomerText);
		},

		async setInitialCustomerDisplay(customerId) {
			if (!customerId) return;

			try {
				const res = await api.getCustomers(null, customerId);
				if (res.data.message && res.data.message.length > 0) {
					const customer = res.data.message[0];
					this.searchCustomerText = customer.customer_name || customer.name;
				}
			} catch (error) {
				console.error("Failed to fetch initial customer display:", error);
				this.searchCustomerText = customerId; 
			}
		},

		selectCustomer(customer) {
			this.localFilters.customer = customer.value;
			this.searchCustomerText = customer.label; 
			this.dropdownOpen = false;
			this.customers = []; 
			this.highlightedIndex = -1;
		},

		highlightNext() {
			if (this.highlightedIndex < this.customers.length - 1) this.highlightedIndex++;
		},
		highlightPrev() {
			if (this.highlightedIndex > 0) this.highlightedIndex--;
		},
		selectHighlighted() {
			if (this.highlightedIndex >= 0)
				this.selectCustomer(this.customers[this.highlightedIndex]);
		},

		clearCustomerFilterOnly() {
			this.localFilters.customer = "";
			this.dropdownOpen = false;
			this.customers = [];
			this.highlightedIndex = -1;
		},

		clearCustomer() {
			this.searchCustomerText = "";
			this.clearCustomerFilterOnly();
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
			this.dropdownOpen = false;
			const filtersToApply = { ...this.localFilters };
			this.$emit("apply-filters", filtersToApply);
		},

		outsideClick(e) {
			if (this.$el && !this.$el.contains(e.target)) {
				this.dropdownOpen = false;
			}
		},
	},

	mounted() {
		this.debouncedFetchCustomers = this.debounce(this.fetchCustomers, 300);

		if (this.localFilters.customer) {
			this.setInitialCustomerDisplay(this.localFilters.customer);
		}
		document.addEventListener("click", this.outsideClick);
	},

	beforeUnmount() {
		document.removeEventListener("click", this.outsideClick);
	},
};
</script>

