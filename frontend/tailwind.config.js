import flowbite from "flowbite/plugin";

/** @type {import('tailwindcss').Config} */
export default {
	prefix: "mss-",
	corePlugins: {
		preflight: false, // ❌ disable global reset
	},
	content: [
		"./index.html",
		"./src/**/*.{vue,js,ts,jsx,tsx,html}",
		"./node_modules/flowbite/**/*.js",
	],
	theme: {
		extend: {},
	},
	plugins: [flowbite],
};
