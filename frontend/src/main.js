import { createApp } from "vue";
import MSSDashboard from "./pages/MSSDashboard.vue";
import "./style.css";

window.initVueApp = function () {
    const app = createApp(MSSDashboard);
    app.mount("#mss-vue-app");
    console.log("Vue app mounted successfully ✔️");
};
