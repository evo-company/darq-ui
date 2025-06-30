import {
  Button,
  Card,
  Popover,
  Space,
  Statistic,
  Table,
  Tag,
  Input,
} from "antd";
import { useState } from "react";
import { useSearchParams as useSearchParamsDom } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import {
  RemoveTaskFromDroplistButton,
  RunTaskButton,
  DropTaskButton,
} from "./buttons.jsx";

import { TASK_STATUS, TASK_STATUSES_COLOR_SCHEME } from "../constants.js";
import { InfoIcon, LinkIcon, ReloadIcon } from "../icons";
import { getCall } from "../http";
import { getConfig } from "../config";

const StatusDescription = () => (
  <div>
    {[
      {
        status: null,
        description: "Task is ready to be executed",
      },
      {
        status: TASK_STATUS.RUNNING,
        description: "Task is currently executing",
      },
      {
        status: TASK_STATUS.DROPPED,
        description:
          "Task has been added to droplist and no more instances can be scheduled",
      },
    ].map((item) => (
      <p key={item.status}>
        <Tag color={TASK_STATUSES_COLOR_SCHEME[item.status]}>{item.status}</Tag>
        {item.description}
      </p>
    ))}
  </div>
);

const formatSignature = (sig) =>
  sig
    .slice(1, sig.length - 1)
    .split(",")
    .map((s) => s.trim())
    .join("\n");
const formatDoc = (doc) =>
  doc
    .trim()
    .split("\n")
    .map((s) => s.trim())
    .join("\n");

const TaskInfo = ({ task }) => (
  <Space direction="vertical">
    <div>Status: {task.status || "N/A"}</div>
    <div>Queue: {task.queue || "N/A"}</div>
    <div>
      Signature: <pre>{formatSignature(task.signature)}</pre>
    </div>
    <div>
      Doc: <pre>{formatDoc(task.docstring)}</pre>
    </div>
    {task.status === TASK_STATUS.DROPPED && (
      <div>Dropped reason: {task.dropped_reason || "Not specified"}</div>
    )}
    <div>
      <LogsLink taskName={task.name} />
    </div>
  </Space>
);

const TASKNAME_PLACEHOLDER = "${taskName}";

const LogsLink = ({ taskName }) => {
  const config = getConfig();
  const logsUrl = config.logs_url?.replaceAll(TASKNAME_PLACEHOLDER, taskName);
  return (
    <a target="_blank" rel="noreferrer" href={logsUrl}>
      <Space>
        <LinkIcon /> Logs
      </Space>
    </a>
  );
};

const TasksTable = ({ tasks, loading, refetch }) => {
  return (
    <Table
      bordered
      loading={loading}
      dataSource={tasks.map((task) => ({
        key: task.name,
        ...task,
      }))}
      expandable={{
        expandedRowRender: (record) => <TaskInfo task={record} />,
        columnTitle: () => (
          <Button
            type="primary"
            shape="circle"
            icon={<ReloadIcon />}
            size="small"
            loading={loading}
            onClick={() => refetch()}
          />
        ),
      }}
    >
      <Table.Column title="Name" dataIndex="name" />
      <Table.Column
        width={100}
        title={
          <Space align="center">
            Status
            <Popover
              placement="leftTop"
              title="Statuses description:"
              content={<StatusDescription />}
            >
              <InfoIcon />
            </Popover>
          </Space>
        }
        dataIndex={"status"}
        render={(status) => (
          <Tag color={TASK_STATUSES_COLOR_SCHEME[status]}>
            {status} {status === TASK_STATUS.STOPPING ? "..." : ""}
          </Tag>
        )}
      />
      <Table.Column
        width={80}
        title={"Logs"}
        dataIndex={"name"}
        render={(name) => <LogsLink taskName={name} />}
      />
      <Table.Column
        title={"Action"}
        render={(task) => (
          <Space>
            {(() => {
              let buttons = [];

              if (task.status === TASK_STATUS.RUNNING) {
                buttons.push(
                  <DropTaskButton key="drop" taskName={task.name} />,
                );
              } else if (task.status === TASK_STATUS.DROPPED) {
                buttons.push(
                  <RemoveTaskFromDroplistButton
                    key="removeTaskFromDroplist"
                    taskName={task.name}
                  />,
                );
              } else if (task.status === null) {
                buttons.push(<RunTaskButton key="run" task={task} />);
              }

              return buttons;
            })()}
          </Space>
        )}
      />
    </Table>
  );
};

const filterTasks = (tasks, searchTerm) => {
  if (!searchTerm) {
    return tasks;
  }
  return tasks.filter((task) => task.name.includes(searchTerm || ""));
};

// Custom hook to read and update the search params with iframe-mode support.
// If the app is not embedded, it will use the default useSearchParamsDom hook.
// Otherwise, it will use/mutate the parent window location search params.
const useSearchParams = () => {
  const [searchParamsDom, setSearchParamsDom] = useSearchParamsDom();
  if (!getConfig().embed) {
    return [searchParamsDom, setSearchParamsDom];
  }

  const searchParams = new URLSearchParams(window.parent.location.search);
  const setSearchParams = (fn) => {
    const newParams = fn(searchParams);
    window.parent.location.search = newParams.toString();
  };

  return [searchParams, setSearchParams];
};

export const TasksControlPanel = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const defaultSearch = searchParams.get("search");
  const [searchTerm, setSearchTerm] = useState(defaultSearch);

  const { isPending, isError, data, error, refetch } = useQuery({
    queryKey: ["tasks"],
    queryFn: () => getCall("/api/tasks"),
  });

  const loading = isPending;

  if (isError) {
    console.error("Error while fetching tasks", error);
  }

  const tasks = filterTasks(data?.tasks || [], searchTerm);
  const running = tasks.filter((t) => t.status === TASK_STATUS.RUNNING).length;

  return (
    <>
      <Card>
        <Space direction="vertical">
          <Statistic
            loading={loading}
            title="Tasks running"
            value={running}
            valueStyle={{ color: "#3f8600" }}
          />

          <Input.Search
            placeholder={"Enter task name ..."}
            allowClear
            onChange={(e) => {
              setSearchTerm(e.target.value);
            }}
            onSearch={(value, e, info) => {
              setSearchParams((params) => {
                if (info.source === "clear") {
                  params.delete("search");
                } else {
                  params.set("search", value);
                }
                return params;
              });
              setSearchTerm(value);
            }}
            defaultValue={defaultSearch}
            style={{
              width: "500px",
            }}
          />
        </Space>
      </Card>
      <TasksTable
        data={data}
        tasks={tasks}
        loading={loading}
        refetch={refetch}
      />
    </>
  );
};
