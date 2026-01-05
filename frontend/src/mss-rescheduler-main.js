import { createApp } from "vue";
import MSSReschedulerPage from "./pages/MSSReschedulerPage.vue";
import "./style.css";

window.initMSSRescheduler = function () {
    const app = createApp(MSSReschedulerPage);
    app.mount("#mss-rescheduler-vue-app");
    console.log("MSS Rescheduler page mounted successfully ✔️");
};

// Backwards compatibility
window.mountMSSReschedulerVue = window.initMSSRescheduler;



