import React from "react";
import { Link, Navigate } from "react-router-dom";

import { Typography, Result } from "antd";

// import { useAppContext } from "../AppContext";

export const Auth = () => {
  // const context = useAppContext();

  // if (context?.currentUser) {
  //   return <Navigate to="/" replace />;
  // }

  // const authUrl = `https://my.${context.domain}/sign-in`;
  // const authUrlWithNext = `${authUrl}?next=/vidhuk/admin`;

  return (
    <Result
      status="403"
      title="Ви не авторизовані"
      subTitle={
        <Link to={authUrlWithNext} target="_blank" component={Typography.Link}>
          Будь ласка, авторизуйтесь
        </Link>
      }
    />
  );
};
