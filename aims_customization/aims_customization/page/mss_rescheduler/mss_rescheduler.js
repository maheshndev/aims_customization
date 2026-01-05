frappe.pages['mss-rescheduler'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'MSS Re-Scheduler',
		single_column: true
	});

 // Render HTML template
    wrapper.innerHTML = frappe.render_template("mss_rescheduler");

	// Load CSS
    if (!document.querySelector("#mss-vue-css")) {
        const link = document.createElement("link");
        link.id = "mss-vue-css";
        link.rel = "stylesheet";
        link.href = "/assets/aims_customization/mss-vue-app/style.css";
        document.head.appendChild(link);
    }
// Load Vue JS module
    if (!document.querySelector("#mss-vue-script")) {
        const script = document.createElement("script");
        script.id = "mss-vue-script";
        script.type = "module";
        script.src = "/assets/aims_customization/mss-vue-app/mss-rescheduler-main.js";

        // Mount Vue after script loads
        script.onload = () => {
            if (window.initMSSRescheduler) {
                window.initMSSRescheduler();
                console.log("Monthly Capacity Vue app mounted successfully ✔️");
            } else {
                console.error("Vue mount function not found after script loaded");
            }
        };

        script.onerror = () => {
            frappe.msgprint("Failed to load MSS Vue App");
            console.error("Failed to load mss-rescheduler-main.js");
        };

        document.body.appendChild(script);
    }
}
