import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import path from "path";


export default defineConfig({
	plugins: [
		vue()
	],
	// final public path served by frappe
	base: "/assets/mss-vue-app/",

	build: {
		// IMPORTANT: build inside frappe app
		outDir: path.resolve(__dirname, "../aims_customization/mss-vue-app"),
		emptyOutDir: true,

		rollupOptions: {
			input: path.resolve(__dirname, "src/main.js"),
			output: {
				entryFileNames: "main.js",
				chunkFileNames: "[name].js",
				assetFileNames: "[name].[ext]",
			},
		},
	},
});
