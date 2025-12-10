import { createApp } from "vue";
import MSSDashboard from "./pages/MSSDashboard.vue";

window.initVueApp = function () {
    const app = createApp(MSSDashboard);
    app.mount("#mss-vue-app");
    console.log("Vue app mounted successfully ✔️");
};
