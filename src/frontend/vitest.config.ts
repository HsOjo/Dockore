import { defineConfig } from "vitest/config";
import vue from "@vitejs/plugin-vue";
import { resolve } from "path";
import { readFileSync } from "fs";

const version = readFileSync(resolve(__dirname, "../../VERSION"), "utf-8").trim();

export default defineConfig({
  plugins: [vue()],
  define: {
    __DOCKORE_VERSION__: JSON.stringify(version),
  },
  test: {
    environment: "jsdom",
    exclude: ["e2e/**", "playwright.config.ts", "node_modules/**"],
  },
  resolve: {
    alias: {
      "@": resolve(__dirname, "src"),
    },
  },
});
