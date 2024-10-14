import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App, AppEmbed } from "./App";
import { getConfig } from "./config";


createRoot(document.getElementById("root")).render(
  <StrictMode>
    {getConfig().embed ? <AppEmbed /> : <App />}
  </StrictMode>,
);
