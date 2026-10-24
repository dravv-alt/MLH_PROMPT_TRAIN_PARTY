import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { ClerkProvider } from "@clerk/react";
import App from "./App";
import "./index.css";

const app = <BrowserRouter><App /></BrowserRouter>;
const publishableKey = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY;

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    {publishableKey ? <ClerkProvider publishableKey={publishableKey}>{app}</ClerkProvider> : app}
  </React.StrictMode>
);
