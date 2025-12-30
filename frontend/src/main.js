import { createApp } from "vue";
import MSSDashboard from "./pages/MSSDashboard.vue";
import "./style.css";

window.initMSSDashboard = function () {
    const app = createApp(MSSDashboard);
    app.mount("#mss-vue-app");
    console.log("MSS Dashboard mounted successfully ✔️");
};

// Backwards compatibility
window.initVueApp = window.initMSSDashboard;


