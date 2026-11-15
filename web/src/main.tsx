import React from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import "leaflet/dist/leaflet.css";
import "./styles.css";

const container = document.getElementById("root");
if (container === null) {
  throw new Error("Missing root container");
}
createRoot(container).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
