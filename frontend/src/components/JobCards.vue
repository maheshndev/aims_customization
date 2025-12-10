<template>
	<div class="job-cards rounded shadow-sm p-4">
		
		<!-- Loading -->
		<div v-if="loading" class="text-gray-500">Loading Job Cards...</div>

		<!-- Error -->
		<div v-if="error" class="text-red-500 mb-2">{{ error }}</div>

		<!-- Table -->
		<div v-if="jobCards.length" class="overflow-auto rounded-b-2xl">
			<table class="table-auto min-w-[1200px] border-collapse">
				<thead class="bg-gray-100">
					<tr>
						<th class="border px-3 py-2 text-left">JC</th>
						<th class="border px-3 py-2 text-left">WO</th>
						<th class="border px-3 py-2 text-left">Item</th>
						<th class="border px-3 py-2 text-left">Qty</th>
						<th class="border px-3 py-2 text-left">Status</th>
					</tr>
				</thead>
				<tbody>
					<tr
						v-for="jc in jobCards"
						:key="jc.name"
						class="hover:bg-gray-50"
					>
						<td class="border px-3 py-2">{{ jc.jc_no }}</td>
						<td class="border px-3 py-2">{{ jc.wo_no }}</td>
						<td class="border px-3 py-2">{{ jc.item_name }}</td>
						<td class="border px-3 py-2">{{ jc.qty }}</td>
						<td class="border px-3 py-2">{{ jc.status }}</td>
					</tr>
				</tbody>
			</table>
		</div>

		<!-- No Data -->
		<div v-if="!jobCards.length && !loading" class="text-gray-500 mt-2">
			No Job Cards found.
		</div>
	</div>
</template>

<script>
import {api} from "../services/api"

export default {
	name: "JobCards",

	props: {
		workOrders: { type: Array, default: () => [] }
	},

	data() {
		return {
			jobCards: [],
			loading: false,
			error: null
		};
	},

	methods: {
		async fetchJobCards() {
			if (!this.workOrders.length) {
				this.jobCards = [];
				return;
			}

			this.loading = true;
			this.error = null;

			try {
				const res = api.getJobCards(props.workOrders)

				this.jobCards = res.data.message || [];
			} catch (err) {
				console.error(err);
				this.error = "Failed to fetch Job Cards.";
			} finally {
				this.loading = false;
			}
		}
	},

	watch: {
		workOrders: {
			handler() {
				this.fetchJobCards();
			},
			deep: true,
			immediate: true
		}
	}
};
</script>
