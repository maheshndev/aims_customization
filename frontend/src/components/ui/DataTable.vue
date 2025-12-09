<template>
	<div class="overflow-x-auto">
		<table class="min-w-full border border-gray-200">
			<thead class="bg-gray-100">
				<tr>
					<th v-for="col in columns" :key="col.key" class="px-3 py-2 text-left">
						{{ col.label }}
					</th>
				</tr>
			</thead>
			<tbody>
				<tr v-for="(row, idx) in rows" :key="idx" class="border-t">
					<td v-for="col in columns" :key="col.key" class="px-3 py-2">
						{{ row[col.key] }}
					</td>
				</tr>
			</tbody>
		</table>
	</div>
</template>

<script>
export default {
	props: { columns: Array, rows: Array },
};
</script>
