import {
  Button,
  Input,
  message,
  Tooltip,
  Popover,
  Space,
  Tabs,
  Typography,
} from "antd";
import isPlainObject from "lodash/isPlainObject";
import { useEffect, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { postCall } from "../http";

const sayInvalidArgs = (value, err) => {
  message.error(`args "${value}" is invalid JSON array: ${err}`);
};

const sayInvalidKwargs = (value, err) => {
  message.error(`kwargs "${value}" is invalid JSON: ${err}`);
};

const validateArgs = (argsRaw) => {
  if (argsRaw === "" || argsRaw === null) {
    return [];
  }

  if (Array.isArray(argsRaw)) {
    return argsRaw;
  }

  let args = [];
  try {
    let res = JSON.parse(argsRaw);
    if (!Array.isArray(res)) {
      sayInvalidArgs(argsRaw, "not an array");
      return null;
    }
    args = res;
  } catch (e) {
    sayInvalidArgs(argsRaw, e);
    return null;
  }

  return args;
};

const validateKwargs = (kwargsRaw) => {
  if (kwargsRaw === "" || kwargsRaw === null) {
    return {};
  }

  if (isPlainObject(kwargsRaw)) {
    return kwargsRaw;
  }

  let kwargs = {};

  try {
    let res = JSON.parse(kwargsRaw);
    if (!isPlainObject(res)) {
      sayInvalidKwargs(kwargsRaw, "not a plain object");
      return null;
    }
    kwargs = res;
  } catch (e) {
    sayInvalidKwargs(kwargsRaw, e);
    return null;
  }

  return kwargs;
};

const JsonArgsView = ({ task, onClick, setArgs, setKwargs }) => {
  return (
    <Space direction="vertical" style={{ width: "390px" }}>
      <div>Task signature: {task.signature}</div>
      <Input
        label="Positional args"
        placeholder="[123, true]"
        onChange={(e) => setArgs(e.target.value)}
      />
      <Input
        label="Keyword args"
        placeholder={'{"company_id": 123, "dry_run": true}'}
        onChange={(e) => setKwargs(e.target.value)}
      />

      <Button onClick={onClick} type="primary">
        Run
      </Button>
    </Space>
  );
};

const invalid = Symbol("__invalid_value__");

/**
 * Parse python function signature like this:
 * (last_id: int = 0, dry_run: bool = True, batch: int = 0, batch_size: int = 500)
 */
const parseSignature = (signature) => {
  let sig = signature.slice(1, -1); // remove brackets
  return sig.split(",").map((arg) => {
    const [name, rest] = arg.split(":").map((x) => x.trim());
    const type = rest.split(" ")[0];
    const defaultValueRaw = rest.split(" ")[2];
    const defaultValue =
      {
        True: "true",
        False: "false",
        None: "null",
      }[defaultValueRaw] || defaultValueRaw;

    const parse = (value) => {
      if (value === "") {
        return defaultValue;
      }
      switch (type) {
        case "int":
          let parsed = parseInt(value);
          if (isNaN(parsed)) {
            return invalid;
          }
          return parsed;
        case "float":
          parsed = parseFloat(value);
          if (isNaN(parsed)) {
            return invalid;
          }
          return parsed;
        case "bool":
          if (value === "true" || value === "True") {
            return true;
          }
          if (value === "false" || value === "False") {
            return false;
          }
          return invalid;
        default:
          return value;
      }
    };

    return { name, type, defaultValue, parse };
  });
};

const InputArgsView = ({ task, onClick, kwargs, setKwargs }) => {
  const argInputs = [];
  let initialKwargs = {};

  try {
    initialKwargs = JSON.parse(kwargs);
  } catch (e) {
    // start with empty kwargs
  }

  const [localKwargs, setLocalKwargs] = useState(initialKwargs);

  const onSetLocalKwargs = (arg, rawValue) => {
    setLocalKwargs((kw) => {
      if (rawValue === "") {
        delete kw[arg.name];
        return { ...kw };
      }
      let value = arg.parse(rawValue);

      if (value === invalid) {
        return { ...kw };
      }

      return {
        ...kw,
        [arg.name]: value,
      };
    });
  };

  useEffect(() => {
    setKwargs(JSON.stringify(localKwargs));
  }, [localKwargs]);

  const args = parseSignature(task.signature);

  args.forEach((arg, i) => {
    argInputs.push(
      <Space>
        <Typography.Text>{`${arg.name} (${arg.type})`}</Typography.Text>
        <Input
          key={i}
          label={`${arg.name} (${arg.type})`}
          placeholder={arg.defaultValue}
          onChange={(e) => onSetLocalKwargs(arg, e.target.value)}
        />
      </Space>,
    );
  });

  return (
    <Space direction="vertical" style={{ width: "390px" }}>
      <div>Task signature: {task.signature}</div>
      {argInputs}
      <Input
        label="Result keyword args"
        value={kwargs}
        onChange={(e) => setKwargs(e.target.value)}
      />

      <Button onClick={onClick} type="primary">
        Run
      </Button>
    </Space>
  );
};

const ARGS_TABS = {
  JSON: "json",
  INPUT: "input",
};

const ArgsView = ({ task, onClick, args, kwargs, setArgs, setKwargs }) => {
  
    const [argsTab, setArgsTab] = useState(ARGS_TABS.JSON);
    return (
      <Tabs
        defaultActiveKey={ARGS_TABS.JSON}
        activeKey={argsTab}
        onChange={(key) => setArgsTab(key)}
        items={[
          {
            key: ARGS_TABS.JSON,
            label: "JSON",
            children: (
              <JsonArgsView
                task={task}
                onClick={onClick}
                setArgs={setArgs}
                setKwargs={setKwargs}
              />
            ),
          },
          {
            key: ARGS_TABS.INPUT,
            label: "INPUT (experimental)",
            children: (
              <InputArgsView
                task={task}
                onClick={onClick}
                kwargs={kwargs}
                setKwargs={setKwargs}
              />
            ),
          },
        ]}
      />
    );
  };

  export const RunTaskButton = ({ task }) => {
    const [visible, setVisible] = useState(false);
    const [argsRaw, setArgsRaw] = useState("");
    const [kwargsRaw, setKwargsRaw] = useState("");

    const queryClient = useQueryClient();

    const { mutate, isPending } = useMutation({
      mutationFn: (data) => postCall("/api/tasks/run", data),
      onSuccess: (data, variables) => {
        if (data.error !== null) {
          message.error(data.error);
        } else {
          message.success(`Task started: "${variables.task_name}"`);
        }

        // Invalidate and refetch
        queryClient.invalidateQueries({ queryKey: ["tasks"] });
      },
      onError: (error, variables, context) => {
        console.log("error", error, variables, context);
      },
    });

    const validateAndRun = () => {
      const args = validateArgs(argsRaw);
      if (args === null) {
        return;
      }

      const kwargs = validateKwargs(kwargsRaw);
      if (kwargs === null) {
        return;
      }

      mutate({
        task_name: task.name,
        task_args: args ? JSON.stringify(args) : null,
        task_kwargs: kwargs ? JSON.stringify(kwargs) : null,
      });
      setVisible(false);
    };

    return (
      <Popover
        content={
          <ArgsView
            task={task}
            onClick={validateAndRun}
            args={argsRaw}
            kwargs={kwargsRaw}
            setArgs={setArgsRaw}
            setKwargs={setKwargsRaw}
          />
        }
        placement="bottomLeft"
        title="Enter args"
        trigger="click"
        open={visible}
        onOpenChange={(visible) => {
          setVisible(visible);
        }}
      >
        <Button loading={isPending} type="primary">
          Run
        </Button>
      </Popover>
    );
  };

  const DropReasonView = ({ onClick, setReason }) => {
    return (
      <Space direction="vertical" style={{ width: "390px" }}>
        <Input
          label="Reason"
          placeholder="(example) Bug in task"
          onChange={(e) => setReason(e.target.value)}
        />

        <Button onClick={onClick} danger type="primary">
          Drop
        </Button>
      </Space>
    );
  };

  export const DropTaskButton = ({ taskName }) => {
    const [visible, setVisible] = useState(false);
    const [reason, setReason] = useState("");

    const queryClient = useQueryClient();

    const { mutate, isPending } = useMutation({
      mutationFn: (data) => postCall("/api/tasks/droplist/add", data),
      onSuccess: (data, variables) => {
        if (data.error !== null) {
          message.error(data.error);
        } else {
          message.success(`Task added to drop list: "${variables.task_name}"`);
        }

        // Invalidate and refetch
        queryClient.invalidateQueries({ queryKey: ["tasks"] });
      },
      onError: (error, variables, context) => {
        console.log("error", error, variables, context);
      },
    });

    const validateAndDrop = () => {
      if (reason === null || reason === "") {
        message.error("Reason is required");
        return;
      }

      mutate({ task_name: taskName, reason });
      setVisible(false);
    };

    return (
      <Tooltip title="Adds task to droplist. Task can be run again only when removed from droplist manually">
        <Popover
          content={
            <DropReasonView onClick={validateAndDrop} setReason={setReason} />
          }
          placement="bottomLeft"
          title="Drop task reason"
          trigger="click"
          open={visible}
          onOpenChange={(visible) => {
            setVisible(visible);
          }}
        >
          <Button type="primary" danger loading={isPending}>
            Drop
          </Button>
        </Popover>
      </Tooltip>
    );
  };

  export const RemoveTaskFromDroplistButton = ({ taskName }) => {
    const queryClient = useQueryClient();

    const { mutate, isPending } = useMutation({
      mutationFn: (data) => postCall("/api/tasks/droplist/remove", data),
      onSuccess: (data, variables) => {
        if (data.error !== null) {
          message.error(data.error);
        } else {
          message.success(`Task can be run again: "${variables.task_name}"`);
        }

        // Invalidate and refetch
        queryClient.invalidateQueries({ queryKey: ["tasks"] });
      },
      onError: (error, variables, context) => {
        console.log("error", error, variables, context);
      },
    });

    return (
      <Button
        type="primary"
        danger
        loading={isPending}
        onClick={() => mutate({ task_name: taskName })}
      >
        Remove from droplist
      </Button>
    );
  };
