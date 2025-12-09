<template>
	<div class="p-2 shadow-md border border-gray-200 rounded-lg w-full">
		<!-- Filter Grid -->
		<div class="p-3 grid md:grid-cols-4 gap-3">
			<!-- Customer -->
			<div class="relative grid grid-cols-1">
				<label class="filter-label m-1">Customer</label>

				<input
					type="text"
					v-model="searchCustomer"
					placeholder="Search customer..."
					class="filter-input"
					@focus="dropdownOpen = true"
					@input="dropdownOpen = true"
					@keydown.down.prevent="highlightNext"
					@keydown.up.prevent="highlightPrev"
					@keydown.enter.prevent="selectHighlighted"
					@keydown.esc.prevent="dropdownOpen = false"
				/>

				<!-- Dropdown -->
				<ul
					v-if="dropdownOpen"
					class="absolute border rounded-lg mt-1 z-10 max-h-6 w-20 animate-fadeIn"
				>
					<li
						v-for="(c, index) in filteredCustomers"
						:key="c.value"
						@click="selectCustomer(c)"
						@mouseenter="highlightedIndex = index"
						:class="[
							'px-2 py-2 text-sm cursor-pointer rounded-md transition w-20',
							highlightedIndex === index
								? 'bg-blue-100 text-blue-700'
								: 'hover:bg-gray-100',
						]"
					>
						{{ c.label }}
					</li>

					<li
						v-if="filteredCustomers.length === 0"
						class="px-2 py-2 text-sm text-gray-500 w-20"
					>
						No results found
					</li>
				</ul>
			</div>

			<!-- Month -->
			<div class="relative grid grid-cols-1">
				<label class="filter-label m-1">Month</label>
				<select v-model="localFilters.month" class="filter-input">
					<option value="">Select Month</option>
					<option v-for="m in monthOptions" :key="m.value" :value="m.value">
						{{ m.label }}
					</option>
				</select>
			</div>

			<!-- Year -->
			<div class="relative grid grid-cols-1">
				<label class="filter-label m-1">Year</label>
				<select v-model="localFilters.year" class="filter-input">
					<option value="">Select Year</option>
					<option v-for="y in yearOptions" :key="y" :value="y">
						{{ y }}
					</option>
				</select>
			</div>

			<!-- Blanket Orders -->

			<div class="relative grid grid-cols-1">
				<label class="filter-label m-1">Blanket Order</label>

				<input
					type="text"
					v-model="searchBlanketOrder"
					placeholder="Search blanket order..."
					class="filter-input pr-10"
					@focus="boDropdownOpen = true"
					@input="boDropdownOpen = true"
					@keydown.down.prevent="highlightNext"
					@keydown.up.prevent="highlightPrev"
					@keydown.enter.prevent="selectHighlightedBlanketOrder"
					@keydown.esc.prevent="boDropdownOpen = false"
				/>

				<!-- Dropdown -->
				<ul
					v-if="boDropdownOpen"
					class="absolute left-0 right-0 border border-gray-300 rounded-lg shadow-lg mt-1 z-10 max-h-6 overflow-y-auto animate-fadeIn"
				>
					<li
						v-for="(b, index) in filteredBlanketOrders"
						:key="b.value"
						@click="selectBlanketOrder(b)"
						@mouseenter="highlightedIndex = index"
						:class="[
							'px-2 py-2 text-sm cursor-pointer rounded-md transition',
							highlightedIndex === index
								? 'bg-blue-100 text-blue-700'
								: 'hover:bg-gray-100',
						]"
					>
						{{ b.label }}
					</li>

					<li
						v-if="filteredBlanketOrders.length === 0"
						class="px-2 py-2 text-sm text-gray-500"
					>
						No results found
					</li>
				</ul>
			</div>
		</div>

		<!-- Action Buttons -->
		<div class=" flex justify-end gap-1 mt-1">
			<button class="bg-blue-500 hover:bg-blue-700 text-black font-bold py-1 px-1 m-1 rounded" @click="resetFilters">Reset</button>
			<button class="bg-blue-500 hover:bg-blue-700 text-black font-bold py-1 px-1 m-1 rounded" @click="onApplyFilters">Apply Filters</button>
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
			blanketOrders: [],
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
				c.label.toLowerCase().includes(this.searchCustomer.toLowerCase()),
			);
		},
		filteredBlanketOrders() {
			if (!this.searchBlanketOrder)
				return this.blanketOrders.map((b) => ({
					value: b.name,
					label: `${b.name} — ${b.customer_name}`,
				}));

			return this.blanketOrders
				.filter(
					(b) =>
						b.name.toLowerCase().includes(this.searchBlanketOrder.toLowerCase()) ||
						b.customer_name
							.toLowerCase()
							.includes(this.searchBlanketOrder.toLowerCase()),
				)
				.map((b) => ({
					value: b.name,
					label: `${b.name} — ${b.customer_name}`,
				}));
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

		async fetchBlanketOrders() {
			const res = await api.getBlanketOrdersSearch(this.searchBlanketOrder);
			this.blanketOrders = res.data.message;
		},

		selectCustomer(customer) {
			this.localFilters.customer = customer.value;
			this.searchCustomer = customer.label;
			this.dropdownOpen = false;
		},
		selectBlanketOrder(bo) {
			this.localFilters.blanket_order = bo.value;
			this.searchBlanketOrder = bo.label;
			this.boDropdownOpen = false;
		},

		highlightNext() {
			if (this.highlightedIndex < this.filteredCustomers.length - 1) {
				this.highlightedIndex++;
			}
		},

		highlightPrev() {
			if (this.highlightedIndex > 0) {
				this.highlightedIndex--;
			}
		},

		selectHighlighted() {
			if (this.highlightedIndex >= 0) {
				this.selectCustomer(this.filteredCustomers[this.highlightedIndex]);
			}
		},

		resetFilters() {
			this.localFilters = {
				customer: "",
				month: "",
				year: "",
				blanket_order: "",
				search: "",
			};
			this.searchCustomer = "";
		},

		onApplyFilters() {
			this.$emit("apply-filters", this.localFilters);
		},

		outsideClick(e) {
			if (!this.$el.contains(e.target)) this.dropdownOpen = false;
		},
	},

	mounted() {
		this.fetchCustomers();
		this.fetchBlanketOrders();
		document.addEventListener("click", this.outsideClick);
	},

	beforeUnmount() {
		document.removeEventListener("click", this.outsideClick);
	},
};
</script>

<style scoped>

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
</style>
