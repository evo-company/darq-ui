import { HashRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import "./App.css";

import { Base, BaseEmbed } from "./Base.jsx";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false, // default: true
    },
  },
});

export function App() {
  return (
    <HashRouter>
      <QueryClientProvider client={queryClient}>
        <Base />
      </QueryClientProvider>
    </HashRouter>
  );
}

// TODO: search params does not work in iframe
export function AppEmbed() {
  return (
    <HashRouter>
      <QueryClientProvider client={queryClient}>
        <BaseEmbed />
      </QueryClientProvider>
    </HashRouter>
  );
}
