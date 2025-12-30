<template>
  <div class="p-4 shadow-sm border border-gray-200 rounded-lg bg-white relative">
    <p>Select Year, Month, and Customer for Production Planning</p>

    <div class="flex flex-wrap gap-4 mt-2">

      <!-- Year Selector -->
      <div class="relative flex-1 min-w-[150px] max-w-[200px]">
        <label class="block text-sm font-medium text-gray-700 mb-1">Year</label>
        <div class="relative">
          <select v-model="localFilters.year"
                  class="w-full h-9 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 pr-2 pl-2 text-sm">
            <option value="">Select Year</option>
            <option v-for="y in yearOptions" :key="y" :value="y">{{ y }}</option>
          </select>
          <span v-if="localFilters.year" @click="clearYear"
                class="absolute right-2 top-1/2 transform -translate-y-1/2 cursor-pointer text-gray-400 hover:text-gray-700">✕</span>
        </div>
      </div>

      <!-- Month Selector -->
      <div class="relative flex-1 min-w-[150px] max-w-[200px]">
        <label class="block text-sm font-medium text-gray-700 mb-1">Month</label>
        <div class="relative">
          <select v-model="localFilters.month"
                  class="w-full h-9 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 pr-2 pl-2 text-sm">
            <option value="">Select Month</option>
            <option v-for="m in monthOptions" :key="m.value" :value="m.value">{{ m.label }}</option>
          </select>
          <span v-if="localFilters.month" @click="clearMonth"
                class="absolute right-2 top-1/2 transform -translate-y-1/2 cursor-pointer text-gray-400 hover:text-gray-700">✕</span>
        </div>
      </div>

      <!-- Customer Search -->
      <div class="relative flex-3 min-w-[300px] max-w-[400px]">
        <label class="block text-sm font-medium text-gray-700 mb-1">Customer</label>
        <div class="relative">
          <input type="text"
                 v-model="searchCustomerText"
                 placeholder="Search customer..."
                 class="w-full h-9 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 pr-2 pl-2 text-sm"
                 @focus="handleCustomerFocus"
                 @input="handleCustomerInput"
                 @keydown.down.prevent="highlightNext"
                 @keydown.up.prevent="highlightPrev"
                 @keydown.enter.prevent="selectHighlighted"
                 @keydown.esc.prevent="dropdownOpen = false" />
          <span v-if="localFilters.customer || searchCustomerText" @click="clearCustomer"
                class="absolute right-2 top-1/2 transform -translate-y-1/2 cursor-pointer text-gray-400 hover:text-gray-700">✕</span>
        </div>

        <!-- Dropdown -->
        <ul v-if="dropdownOpen"
            class="absolute left-0 w-full border border-gray-300 rounded-md shadow-lg mt-1 z-10 max-h-60 overflow-y-auto bg-white">
          <li v-if="customerSearchLoading" class="px-3 py-2 text-sm text-gray-500 flex items-center">
            Searching...
          </li>
          <li v-for="(c, index) in customers" :key="c.value"
              @click="selectCustomer(c)"
              @mouseenter="highlightedIndex = index"
              :class="['px-3 py-2 text-sm cursor-pointer transition border-b last:border-b-0',
                       highlightedIndex === index ? 'bg-blue-100 text-blue-700' : 'hover:bg-gray-50']">
            {{ c.label }}
          </li>
          <li v-if="!customerSearchLoading && customers.length === 0" class="px-3 py-2 text-sm text-gray-500">
            No customers found matching "{{ searchCustomerText }}"
          </li>
        </ul>
      </div>
    </div>

    <!-- Buttons -->
    <div class="flex justify-start gap-3 mt-3 pt-2">
      <button class="flex items-center justify-center bg-gray-50 hover:bg-gray-100 border border-gray-300 text-gray-700 font-semibold py-1.5 px-4 rounded shadow-sm transition duration-150"
              @click="resetFilters">
        Reset All
      </button>
      <button class="flex items-center justify-center bg-blue-600 hover:bg-blue-700 text-white font-semibold py-1.5 px-4 rounded shadow-md transition duration-150"
              @click="applyFilters">
        Apply Filters
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount } from "vue";
import { api } from "../services/capavityApi";

/* ✅ FIX: assign defineProps to variable */
const props = defineProps({
  modelValue: {
    type: Object,
    required: true
  }
});

const emit = defineEmits(["update:modelValue", "apply-filters"]);

/* State */
const localFilters = ref({ ...props.modelValue });
const dropdownOpen = ref(false);
const searchCustomerText = ref("");
const customers = ref([]);
const highlightedIndex = ref(-1);
const customerSearchLoading = ref(false);

let debouncedFetchCustomers = null;

/* Options */
const monthOptions = [
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
  { value: "12", label: "December" }
];

const yearOptions = Array.from(
  { length: 6 },
  (_, i) => new Date().getFullYear() - 2 + i
);

/* Sync v-model */
watch(
  localFilters,
  (val) => emit("update:modelValue", val),
  { deep: true }
);

watch(
  () => props.modelValue,
  (val) => (localFilters.value = { ...val }),
  { deep: true }
);

/* Utils */
const debounce = (fn, delay) => {
  let t;
  return (...args) => {
    clearTimeout(t);
    t = setTimeout(() => fn(...args), delay);
  };
};

/* API */
const fetchCustomers = async (text = "") => {
  customerSearchLoading.value = true;
  try {
    const res = await api.getCustomerList(text);
    customers.value = res.data.message.map(c => ({
      value: c.name,
      label: c.customer_name || c.name
    }));
  } catch {
    customers.value = [];
  } finally {
    customerSearchLoading.value = false;
  }
};

/* Handlers */
const handleCustomerFocus = async () => {
  dropdownOpen.value = true;
  if (!searchCustomerText.value && !customers.value.length) {
    await fetchCustomers("");
  }
};

const handleCustomerInput = () => {
  localFilters.value.customer = "";
  debouncedFetchCustomers(searchCustomerText.value);
};

const selectCustomer = (c) => {
  localFilters.value.customer = c.value;
  searchCustomerText.value = c.label;
  dropdownOpen.value = false;
  customers.value = [];
  highlightedIndex.value = -1;
};

const highlightNext = () => {
  if (highlightedIndex.value < customers.value.length - 1)
    highlightedIndex.value++;
};

const highlightPrev = () => {
  if (highlightedIndex.value > 0)
    highlightedIndex.value--;
};

const selectHighlighted = () => {
  if (highlightedIndex.value >= 0)
    selectCustomer(customers.value[highlightedIndex.value]);
};

const clearCustomer = () => {
  searchCustomerText.value = "";
  localFilters.value.customer = "";
  customers.value = [];
  dropdownOpen.value = false;
};

const clearMonth = () => (localFilters.value.month = "");
const clearYear = () => (localFilters.value.year = "");
const resetFilters = () => {
  clearCustomer();
  clearMonth();
  clearYear();
};

const applyFilters = () =>
  emit("apply-filters", { ...localFilters.value });

/* Outside click */
const outsideClick = (e) => {
  if (!e.target.closest(".relative")) dropdownOpen.value = false;
};

/* Lifecycle */
onMounted(() => {
  debouncedFetchCustomers = debounce(fetchCustomers, 300);
  document.addEventListener("click", outsideClick);
});

onBeforeUnmount(() => {
  document.removeEventListener("click", outsideClick);
});
</script>
