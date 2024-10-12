import { HashRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import "./App.css";

import { Base } from "./Base.jsx";

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
