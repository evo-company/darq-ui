import { Route, Routes } from "react-router-dom";

import { TasksControlPanel } from "../TasksControlPanel";

export const Routing = () => {
  return (
    <Routes>
      <Route index element={<TasksControlPanel />} />
    </Routes>
  );
};
