frappe.pages["mss-schedule-tool"].on_page_load = function (wrapper) {
    frappe.ui.make_app_page({
        parent: wrapper,
        title: "Monthly Schedule Sheet (MSS)",
        single_column: true
    });

    wrapper.innerHTML = frappe.render_template("mss_schedule_tool");
    load_vue_app();
};

function load_vue_app() {
    console.log("Loading MSS Vue App…");
    
    if (!document.querySelector("#mss-vue-css")) {
        const link = document.createElement("link");
        link.id = "mss-vue-css";
        link.rel = "stylesheet";
        link.href = "/assets/aims_customization/mss-vue-app/style.css";
        document.head.appendChild(link);
    }

    const script = document.createElement("script");
    script.type = "module";
    script.src = "/assets/aims_customization/mss-vue-app/main.js";

    script.onload = () => {
        console.log("Vue App JS Loaded ✔️");

        const interval = setInterval(() => {
            const mountDiv = document.querySelector("#mss-vue-app");

            if (mountDiv) {
                console.log("Mount point found, initializing MSS Dashboard…");

                if (window.__MSS_DASHBOARD_MOUNTED__) {
                    clearInterval(interval);
                    return;
                }

                window.__MSS_DASHBOARD_MOUNTED__ = true;
                if (window.initMSSDashboard) {
                    window.initMSSDashboard();
                } else if (window.initVueApp) {
                    // fallback for older builds
                    window.initVueApp();
                }

                clearInterval(interval); // ← stop repeats
            }
        }, 50); // slightly delayed for stability
    };

    script.onerror = () => frappe.msgprint("Failed to load MSS Vue App");

    document.body.appendChild(script);
}
