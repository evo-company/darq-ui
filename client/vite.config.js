import { defineConfig, splitVendorChunkPlugin } from "vite";
import react from "@vitejs/plugin-react";
import vitePluginImp from "vite-plugin-imp";
import { dynamicBase } from 'vite-plugin-dynamic-base'


// https://vitejs.dev/config/
export default defineConfig({
  server: {
    port: 3001,
    proxy: {
      "/api": "http://localhost:3000",
    },
  },
  base: "/__dynamic_base__/",
  plugins: [
    react(),
    splitVendorChunkPlugin(),
    dynamicBase({
      publicPath: 'window.__dynamic_base__',
      transformIndexHtml: true,
    }),
    vitePluginImp({
      optimize: true,
      libList: [
        {
          libName: "antd",
          libDirectory: "es",
          style: (name) => `antd/es/${name}/style`,
        },
      ],
    }),
  ],
});
