import { Layout, Typography, Skeleton } from "antd";
import { useState } from "react";

import { Menu } from "./Menu";
import { Routing } from "./Routing";

const { Header, Content, Sider } = Layout;

const SIDEBAR_KEY = "darq_ui:sidebar";

export const Base = () => {
  const [collapsed, setCollapsed] = useState(
    window.localStorage.getItem(SIDEBAR_KEY) === "true",
  );
  const onCollapse = (isCollapsed) => {
    setCollapsed(isCollapsed);
    window.localStorage.setItem(SIDEBAR_KEY, isCollapsed);
  };

  const loading = false;
  return (
    <Layout
      style={{
        minHeight: "100vh",
      }}
    >
      <Header style={{ padding: "0 24px" }}>
        <Typography.Title
          style={{
            color: "#fff",
            fontSize: "24px",
            fontFamily: "helvetica",
          }}
        >
          Darq UI
        </Typography.Title>
      </Header>
      <Layout>
        <Sider
          collapsible
          collapsed={collapsed}
          width={250}
          onCollapse={onCollapse}
        >
          <Menu />
        </Sider>
        <Content style={{ padding: 24 }}>
          {loading ? <Skeleton /> : <Routing />}
        </Content>
      </Layout>
    </Layout>
  );
};
