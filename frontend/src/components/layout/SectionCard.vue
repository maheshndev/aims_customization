<template>
	<div class="p-4 mb-6">
		<h3 class="text-lg font-semibold mb-3">{{ title }}</h3>
		<slot />
	</div>
</template>

<script>
export default { props: { title: String } };
</script>
<style>
/* only custom overrides here */
</style>
