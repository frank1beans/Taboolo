import { createRoot } from "react-dom/client";
import App from "./App.tsx";
import { client } from "./lib/appwrite";
import "./index.css";

client.ping().catch((error) => {
  console.error("Appwrite ping failed", error);
});

createRoot(document.getElementById("root")!).render(<App />);
