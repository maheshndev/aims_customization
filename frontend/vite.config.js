import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import path from "path";

export default defineConfig({
	plugins: [
		vue()
	],
	resolve: {
    alias: {
      '@fullcalendar/daygrid': path.resolve(__dirname, 'node_modules/@fullcalendar/daygrid'),
    }
  },
	base: "/assets/mss-vue-app/",

	build: {
		
		outDir: path.resolve(__dirname, "../aims_customization/mss-vue-app"),
		emptyOutDir: true,

		rollupOptions: {
			input: {
				main: path.resolve(__dirname, "src/main.js"),
				"mss-cp-main": path.resolve(__dirname, "src/mss-cp-main.js"),
				"mss-rescheduler-main": path.resolve(__dirname, "src/mss-rescheduler-main.js")
			},
			output: {
				entryFileNames: "[name].js",
				chunkFileNames: "[name].js",
				assetFileNames: "[name].[ext]",
			},
		},
	},
});
