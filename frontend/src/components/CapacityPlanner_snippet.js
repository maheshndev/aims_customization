function refreshData() {
	// Clear previous results
	schedulePreview.value = [];
	rows.value.forEach((r) => {
		r.validation_error = null;
		r.capacity_gap = null;
		r.available_hours = null;
		r.required_hours = null;
		r.pcs_per_hour = null;
	});
	preview.value = {};

	// Re-trigger validation or check availability if inputs are valid
	if (validateInputs()) {
		if (modalAction.value === "validate") {
			validateCapacity();
		} else {
			checkAvailability();
		}
		showMessage({
			title: "Refreshed",
			message: "Data refreshed based on new inputs.",
			indicator: "green",
		});
	}
}
