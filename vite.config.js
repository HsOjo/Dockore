import {defineConfig} from 'vite';
import vue from '@vitejs/plugin-vue2'
import vitePluginRequire from 'vite-plugin-require'
import {fileURLToPath, URL} from "url";

// https://vitejs.dev/config
export default defineConfig({
  resolve: {
    alias: [
      {find: '@', replacement: fileURLToPath(new URL('./src', import.meta.url))},
      {find: /~(.+)/, replacement: (_, path) => fileURLToPath(new URL(`./node_modules/${path}`, import.meta.url))},
    ]
  },
  plugins: [vue(), vitePluginRequire()],
});
