import { Route, Routes } from "react-router-dom";

import { Auth } from "../Auth";
import { AuthRequired } from "../Auth/AuthRequired";
import { TasksControlPanel } from "../TasksControlPanel";

export const Routing = () => {
  return (
    <Routes>
      <Route path="/" element={<AuthRequired />}>
        <Route
          index
          element={
            <TasksControlPanel />
          }
        />
      </Route>
      <Route path="/auth" element={<Auth />} />
    </Routes>
  );
};
