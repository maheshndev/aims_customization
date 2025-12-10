<template>
  <div class="work-orders rounded shadow-sm p-4">

    <!-- Loading -->
    <div v-if="loading" class="text-gray-500">Loading Work Orders...</div>

    <!-- Error -->
    <div v-if="error" class="text-red-500 mb-2">{{ error }}</div>

    <!-- Table -->
    <div v-if="workOrders.length" class="overflow-auto rounded-b-2xl">

      <!-- Actions -->
      <div class="flex items-center gap-3 mb-3">
        <button
          class="px-3 py-1 bg-blue-600 text-black rounded hover:bg-blue-700"
          @click="selectAll"
        >
          Select All
        </button>

        <button
          class="px-3 py-1 bg-gray-600 text-black rounded hover:bg-gray-700"
          @click="unselectAll"
        >
          Unselect All
        </button>

        <span class="text-gray-600">
          Selected: {{ selectedWorkOrders.length }}
        </span>
      </div>

      <table class="min-w-[1200px] table-auto w-full border-collapse">
        <thead class="bg-gray-100">
          <tr>
            <th class="border px-3 py-2 text-left">
              <input
                type="checkbox"
                :checked="isAllSelected"
                @change="toggleSelectAll"
              />
            </th>

            <th class="border px-3 py-2 text-left whitespace-nowrap">WO</th>
            <th class="border px-3 py-2 text-left whitespace-nowrap">SO</th>
            <th class="border px-3 py-2 text-left whitespace-nowrap">Item</th>
            <th class="border px-3 py-2 text-left whitespace-nowrap">Qty</th>
            <th class="border px-3 py-2 text-left whitespace-nowrap">Produced Qty</th>
            <th class="border px-3 py-2 text-left whitespace-nowrap">Planned Start Date</th>
            <th class="border px-3 py-2 text-left whitespace-nowrap">Planned End Date</th>
            <th class="border px-3 py-2 text-left whitespace-nowrap">Status</th>
            <th class="border px-3 py-2 text-left whitespace-nowrap">Expected Delivery Date</th>
            <th class="border px-3 py-2 text-left whitespace-nowrap">Stock UOM</th>
            <th class="border px-3 py-2 text-left whitespace-nowrap">Material Transferred</th>
            <th class="border px-3 py-2 text-left whitespace-nowrap">Disassembled Qty</th>
            <th class="border px-3 py-2 text-left whitespace-nowrap">BOM No</th>
            <th class="border px-3 py-2 text-left whitespace-nowrap">FG Warehouse</th>
            <th class="border px-3 py-2 text-left whitespace-nowrap">Scrap Warehouse</th>
            <th class="border px-3 py-2 text-left whitespace-nowrap">WIP Warehouse</th>
            <th class="border px-3 py-2 text-left whitespace-nowrap">Company</th>
          </tr>
        </thead>

        <tbody>
          <tr
            v-for="wo in workOrders"
            :key="wo.name"
            class="hover:bg-gray-50"
          >
            <!-- Row checkbox -->
            <td class="border px-3 py-2 text-center">
              <input
                type="checkbox"
                :value="wo.name"
                v-model="selectedWorkOrders"
                @change="emitSelection"
              />
            </td>

            <td class="border px-3 py-2 whitespace-nowrap">{{ wo.wo_name }}</td>
            <td class="border px-3 py-2 whitespace-nowrap">{{ wo.so_name }}</td>
            <td class="border px-3 py-2 whitespace-nowrap">{{ wo.production_item }}</td>
            <td class="border px-3 py-2 whitespace-nowrap">{{ wo.wo_qty }}</td>
            <td class="border px-3 py-2 whitespace-nowrap">{{ wo.produced_qty }}</td>
            <td class="border px-3 py-2 whitespace-nowrap">{{ wo.planned_start_date }}</td>
            <td class="border px-3 py-2 whitespace-nowrap">{{ wo.planned_end_date }}</td>
            <td class="border px-3 py-2 whitespace-nowrap">{{ wo.status }}</td>
            <td class="border px-3 py-2 whitespace-nowrap">{{ wo.expected_delivery_date }}</td>
            <td class="border px-3 py-2 whitespace-nowrap">{{ wo.stock_uom }}</td>
            <td class="border px-3 py-2 whitespace-nowrap">{{ wo.material_transferred_for_manufacturing }}</td>
            <td class="border px-3 py-2 whitespace-nowrap">{{ wo.disassembled_qty }}</td>
            <td class="border px-3 py-2 whitespace-nowrap">{{ wo.bom_no }}</td>
            <td class="border px-3 py-2 whitespace-nowrap">{{ wo.fg_warehouse }}</td>
            <td class="border px-3 py-2 whitespace-nowrap">{{ wo.scrap_warehouse }}</td>
            <td class="border px-3 py-2 whitespace-nowrap">{{ wo.wip_warehouse }}</td>
            <td class="border px-3 py-2 whitespace-nowrap">{{ wo.company }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- No Data -->
    <div v-if="!workOrders.length && !loading" class="text-gray-500 mt-2">
      No Work Orders found.
    </div>

  </div>
</template>

<script>
import { api } from "../services/api";

export default {
  name: "WorkOrders",

  props: {
    salesOrders: { type: Array, default: () => [] },
  },

  data() {
    return {
      workOrders: [],
      loading: false,
      error: null,

      // NEW: Selected work orders array
      selectedWorkOrders: [],
    };
  },

  computed: {
    isAllSelected() {
      return (
        this.workOrders.length > 0 &&
        this.selectedWorkOrders.length === this.workOrders.length
      );
    },
  },

  methods: {
    async fetchWorkOrders() {
      if (!this.salesOrders.length) {
        this.workOrders = [];
        this.selectedWorkOrders = [];
        return;
      }

      this.loading = true;
      this.error = null;

      try {
        const res = await api.getWorkOrders(this.salesOrders);
        this.workOrders = res.data.message || [];

        // Reset selected WOs when loading
        this.selectedWorkOrders = [];

        this.$emit("wo-loaded", this.workOrders);
      } catch (err) {
        console.error(err);
        this.error = "Failed to fetch Work Orders.";
      } finally {
        this.loading = false;
      }
    },

    toggleSelectAll(e) {
      if (e.target.checked) this.selectAll();
      else this.unselectAll();
    },

    selectAll() {
      this.selectedWorkOrders = this.workOrders.map((wo) => wo.name);
      this.emitSelection();
    },

    unselectAll() {
      this.selectedWorkOrders = [];
      this.emitSelection();
    },

    emitSelection() {
      this.$emit("wo-selected", this.selectedWorkOrders);
    },
  },

  watch: {
    salesOrders: {
      handler() {
        this.fetchWorkOrders();
      },
      deep: true,
      immediate: true,
    },
  },
};
</script>
