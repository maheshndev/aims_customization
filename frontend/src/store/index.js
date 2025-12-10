import { reactive } from "vue";

export const state = reactive({
  filters: {
    customer: "",
    month: "",
    year: new Date().getFullYear(),
  },
  customers: [],
  blanketOrders: [],
  selectedBO: null,
  blanketOrderItems: [],
  selectedItems: [],
  salesOrders: [],
  selectedBOMs: [],
  rawMaterials: [],
  workOrders: [],
  jobCards: [],
  productionSummary: [],
});
