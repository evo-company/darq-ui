import { Layout, Typography } from "antd";

import { Routing } from "./Routing";

import { TasksControlPanel } from "../TasksControlPanel";

const { Header, Content } = Layout;

export const Base = () => {
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
        <Content style={{ padding: 24 }}>
          <Routing />
        </Content>
      </Layout>
    </Layout>
  );
};


export const BaseEmbed = () => {
  return (
    <Layout
      style={{
        minHeight: "100vh",
      }}
    >
      <TasksControlPanel />
    </Layout>
  );
};
