import { createApp } from "vue";
import MSSCapacityMonthlyPage from "./pages/MSSCapacityMonthlyPage.vue";
import "./style.css";

window.initCapacityMonthly = function () {
    const app = createApp(MSSCapacityMonthlyPage);
    app.mount("#monthly-capacity-vue-app");
    console.log("Monthly Capacity page mounted successfully ✔️");
};

// Backwards compatibility
window.mountMonthlyCapacityVue = window.initCapacityMonthly;



