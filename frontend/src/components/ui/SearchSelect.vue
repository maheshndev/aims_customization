<template>
  <div class="relative min-w-[220px]" ref="wrapper">
    <label class="block text-xs text-gray-600 mb-1">
      {{ label }}
    </label>

    <input
      v-model="search"
      @input="onInput"
      @focus="openDropdown"
      class="border rounded px-3 py-1.5 w-full text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
      :placeholder="`Search ${label}`"
    />

    <!-- DROPDOWN -->
    <ul
      v-show="open && options.length"
      class="absolute z-50 mt-1 w-full bg-white border rounded shadow-lg
             max-h-56 overflow-auto text-sm"
    >
      <li
        v-for="opt in options"
        :key="opt"
        @click="select(opt)"
        class="px-3 py-2 cursor-pointer hover:bg-blue-50 whitespace-nowrap"
      >
        {{ opt }}
      </li>
    </ul>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from "vue";
import { mssApi } from "../../services/rescheduleApi";

const props = defineProps({
  label: String,
  doctype: String,
  modelValue: String
});

const emit = defineEmits(["update:modelValue"]);

const wrapper = ref(null);
const search = ref(props.modelValue || "");
const options = ref([]);
const open = ref(false);

// Watch for external changes (e.g. Reset button)
import { watch } from "vue";
watch(() => props.modelValue, (val) => {
  search.value = val || "";
});

async function onInput() {
  open.value = true;
  // If user clears input manually, emit empty
  if (!search.value) {
    emit("update:modelValue", "");
  }
  try {
    const res = await mssApi.search(props.doctype, search.value);
    const responseData = res.data.message;
    if (responseData.success) {
      options.value = responseData.data || [];
    } else {
      console.error("Search failed:", responseData.message);
      options.value = [];
    }
  } catch (e) {
    console.error("Search API Error", e);
    options.value = [];
  }
}

function openDropdown() {
  open.value = true;
  onInput();
}

function select(val) {
  emit("update:modelValue", val);
  search.value = val;
  open.value = false;
}

/* 🔐 Click outside to close */
function handleClickOutside(e) {
  if (wrapper.value && !wrapper.value.contains(e.target)) {
    open.value = false;
  }
}

onMounted(() => {
  document.addEventListener("click", handleClickOutside);
});

onBeforeUnmount(() => {
  document.removeEventListener("click", handleClickOutside);
});
</script>
