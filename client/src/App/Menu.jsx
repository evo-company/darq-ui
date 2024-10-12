import { Menu as AntdMenu } from "antd";
import { Link } from "react-router-dom";

import {
  ControlOutlined,
} from "@ant-design/icons";


function getItem(label, key, icon, children, type) {
  return {
    key,
    icon,
    children,
    label,
    type,
    className: "menu-item",
  };
}

export const Menu = () => {
  return (
    <AntdMenu
      mode="inline"
      theme="dark"
      items={[
        getItem(<Link to="/">Tasks</Link>, "tasks", <ControlOutlined />),
      ]}
    />
  );
};
