/**
 * Extracts a readable error message from a Frappe API error response.
 * @param {Error} err - The error object from axios/fetch.
 * @returns {string} - The extracted error message.
 */
export function extractFrappeError(err) {
	if (!err) return "Unknown Error";

	// Axios error
	if (err.response && err.response.data) {
		const data = err.response.data;

		// Frappe often returns errors in _server_messages
		if (data._server_messages) {
			try {
				const messages = JSON.parse(data._server_messages);
				// messages is usually a list of JSON strings or objects
				return messages
					.map((m) => {
						if (typeof m === "string") return JSON.parse(m).message;
						return m.message;
					})
					.join("\n");
			} catch (e) {
				console.error("Failed to parse _server_messages", e);
			}
		}

		if (data.message) return data.message;
		if (data.exception) return data.exception;
	}

	return err.message || "An unexpected error occurred";
}

/**
 * Displays a message using Frappe's msgprint if available, otherwise fallbacks to alert.
 * @param {Object} options - Message options.
 * @param {string} options.title - Message title.
 * @param {string} options.message - Message body.
 * @param {string} options.indicator - Color indicator (e.g., 'blue', 'red', 'orange', 'green').
 */
export function showMessage({ title, message, indicator = "blue" }) {
	if (window.frappe && window.frappe.msgprint) {
		window.frappe.msgprint({
			title: title,
			message: message,
			indicator: indicator,
		});
	} else {
		console.log(`[${title}] ${message}`);
		// Basic alert fallback
		alert(`${title}: ${message}`);
	}
}
