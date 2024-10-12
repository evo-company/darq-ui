import { HashRouter } from "react-router-dom";
import {
  QueryClient,
  QueryClientProvider,
} from '@tanstack/react-query'

import "./App.css";

// import { ContextProvider } from "./AppContext";

import { Base } from "./Base.jsx";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false, // default: true
    },
  },
});

export function App() {
  // TODO: do we need a hash router ?
  return (
    <HashRouter>
      <QueryClientProvider client={queryClient}>
        {/* <ContextProvider> */}
        <Base />
        {/* </ContextProvider> */}
      </QueryClientProvider>
    </HashRouter>
  );
}

