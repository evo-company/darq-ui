import { Layout, Typography, Skeleton, Result } from "antd";
import { useState } from "react";

import { Menu } from "./Menu";
import { Routing } from "./Routing";

const { Header, Content, Sider } = Layout;

const SIDEBAR_KEY = "darq_ui:sidebar";

// const AccessDenied = () => (
//   <Result status="403" title="Доступ заборонено" />
// );


// TODO: do we need to keep auth here ?
// TODO: maybe drq ui on backend can have auth user info
export const Base = () => {
  // const [context, loading] = useLoadingAppContext();

  // if (
  //   context?.currentUser?.group &&
  //   !BASE_ACCESS_GROUPS.includes(context?.currentUser?.group)
  // ) {
  //   return <AccessDenied />;
  // }
  //
  const [collapsed, setCollapsed] = useState(
    window.localStorage.getItem(SIDEBAR_KEY) === "true"
  );
  const onCollapse = (isCollapsed, type) => {
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
        {/* {context?.currentUser && ( */}
        {/*   <Typography.Text */}
        {/*     style={{ */}
        {/*       color: "#fff", */}
        {/*       fontFamily: "helvetica", */}
        {/*       position: "absolute", */}
        {/*       top: "18px", */}
        {/*       right: "24px", */}
        {/*     }} */}
        {/*   > */}
        {/*     {context?.currentUser?.firstName} {context?.currentUser?.lastName} ( */}
        {/*     {context?.currentUser?.id}) */}
        {/*   </Typography.Text> */}
        {/* )} */}
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
