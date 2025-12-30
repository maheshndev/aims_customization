<template>
	<div class="p-2 mb-4">
		<h3 class="text-lg font-semibold mb-3">{{ title }}</h3>
		<slot />
	</div>
</template>

<script>
export default { props: { title: String } };
</script>

