frappe.pages["mss-schedule-tool"].on_page_load = function (wrapper) {
	frappe.ui.make_app_page({
		parent: wrapper,
		title: "Monthly Schedule Sheet (MSS)",
		single_column: true,
	});

	wrapper.innerHTML = frappe.render_template("mss_schedule_tool");
	load_vue_app();
};

function load_vue_app() {
	console.log("Loading MSS Vue App…");

	// Load CSS (shared across all MSS pages)
	if (!document.querySelector("#mss-vue-css")) {
		const link = document.createElement("link");
		link.id = "mss-vue-css";
		link.rel = "stylesheet";
		link.href = "/assets/aims_customization/mss-vue-app/style.css?v=" + new Date().getTime();
		document.head.appendChild(link);
	}

	const scriptId = "mss-schedule-tool-script";
	const existingScript = document.querySelector(`#${scriptId}`);

	if (!existingScript) {
		const script = document.createElement("script");
		script.id = scriptId;
		script.type = "module";
		script.src = "/assets/aims_customization/mss-vue-app/main.js?v=" + new Date().getTime();

		script.onload = () => {
			console.log("Vue App JS Loaded ✔️");
			mountVueApp();
		};

		script.onerror = () => frappe.msgprint("Failed to load MSS Vue App");

		document.body.appendChild(script);
	} else {
		// Script already loaded, just mount the app
		console.log("Vue App JS already loaded, mounting…");
		mountVueApp();
	}
}

function mountVueApp() {
	const interval = setInterval(() => {
		const mountDiv = document.querySelector("#mss-vue-app");

		if (mountDiv) {
			console.log("Mount point found, initializing MSS Dashboard…");

			// Reset the mounted flag to allow re-mounting
			window.__MSS_DASHBOARD_MOUNTED__ = false;

			if (window.initMSSDashboard) {
				window.initMSSDashboard();
				window.__MSS_DASHBOARD_MOUNTED__ = true;
			} else if (window.initVueApp) {
				// fallback for older builds
				window.initVueApp();
				window.__MSS_DASHBOARD_MOUNTED__ = true;
			}

			clearInterval(interval);
		}
	}, 50); // slightly delayed for stability

	// Safety timeout to prevent infinite interval
	setTimeout(() => clearInterval(interval), 5000);
}
