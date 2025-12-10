import { createRouter, createWebHashHistory } from "vue-router";
import MSSDashboard from "../pages/MSSDashboard.vue";

export default createRouter({
    history: createWebHashHistory(),
    routes: [
        { path: "/", component: MSSDashboard }
    ]
});
