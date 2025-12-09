<!-- create vue componet model dialog-->
<template>
	<div v-if="isVisible" class="modal-overlay" @click.self="close">
		<div class="modal-dialog">
			<header class="modal-header">
				<h2>{{ title }}</h2>
				<button class="close-button" @click="close">&times;</button>
			</header>
			<section class="modal-body">
				<slot></slot>
			</section>
			<footer class="modal-footer">
				<button class="cancel-button" @click="close">Cancel</button>
				<button class="confirm-button" @click="confirm">Confirm</button>
			</footer>
		</div>
	</div>
</template>
<script setup>
import { ref } from "vue";
defineProps({
	title: {
		type: String,
		default: "Modal Title",
	},
	modelValue: {
		type: Boolean,
		default: false,
	},
});
const emit = defineEmits(["update:modelValue", "confirm"]);
const isVisible = ref(props.modelValue);

function close() {
	isVisible.value = false;
	emit("update:modelValue", false);
}

function confirm() {
	emit("confirm");
	close();
}

watch(
	() => props.modelValue,
	(newVal) => {
		isVisible.value = newVal;
	},
);
</script>
