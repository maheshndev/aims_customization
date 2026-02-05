frappe.pages["mss-rescheduler"].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: "MSS Re-Scheduler",
		single_column: true,
	});

	// Render HTML template
	wrapper.innerHTML = frappe.render_template("mss_rescheduler");

	// Load CSS (shared across all MSS pages)
	if (!document.querySelector("#mss-vue-css")) {
		const link = document.createElement("link");
		link.id = "mss-vue-css";
		link.rel = "stylesheet";
		link.href = "/assets/aims_customization/mss-vue-app/style.css?v=" + new Date().getTime();
		document.head.appendChild(link);
	}

	// Load Vue JS module
	const scriptId = "mss-rescheduler-script";
	const existingScript = document.querySelector(`#${scriptId}`);

	if (!existingScript) {
		const script = document.createElement("script");
		script.id = scriptId;
		script.type = "module";
		script.src =
			"/assets/aims_customization/mss-vue-app/mss-rescheduler-main.js?v=" +
			new Date().getTime();

		// Mount Vue after script loads
		script.onload = () => {
			if (window.initMSSRescheduler) {
				window.initMSSRescheduler();
				console.log("MSS Rescheduler Vue app mounted successfully ✔️");
			} else {
				console.error("Vue mount function not found after script loaded");
			}
		};

		script.onerror = () => {
			frappe.msgprint("Failed to load MSS Vue App");
			console.error("Failed to load mss-rescheduler-main.js");
		};

		document.body.appendChild(script);
	} else {
		// Script already loaded, just call mount function
		if (window.initMSSRescheduler) {
			window.initMSSRescheduler();
			console.log("MSS Rescheduler Vue app re-mounted successfully ✔️");
		} else {
			console.error("Vue mount function not found");
		}
	}
};
