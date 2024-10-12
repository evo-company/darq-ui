import React from "react";
import { Outlet, Navigate } from "react-router-dom";

// import { useLoadingAppContext } from "../AppContext";

export const AuthRequired = () => {
  // const [context, loading] = useLoadingAppContext();

  // if (!context?.currentUser && !loading) return <Navigate to="/auth" />;

  return <Outlet />;
};
