import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import { AppProvider } from "./context/AppContext";
import "maplibre-gl/dist/maplibre-gl.css";
import "./styles/app.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <AppProvider>
    <App />
  </AppProvider>,
);
