# darq-ui

## Installation

```bash
pip install darq-ui
```

## Integration

Use `setup` function like this `from darq_ui.integration.<framework> import setup` to integrate darq-ui with your application.

For example, to integrate with FastAPI:

```python
from fastapi import FastAPI
from darq.app import Darq

app = FastAPI()
darq = Darq()

setup(app, darq, base_path="/my-path")
```

### Web UI

Once you have your server running, you can access the web UI at `http://host:port/darq`.

If you wan to change the path, you can pass the `base_path` parameter to the `setup` function:

```python
setup(app, darq, base_path="/my-path")
```

### Logging link 

If you have a logging system such as kibana, you can pass `logs_url` to `setup` function. One requirement is that the url should have the `${taskName}` placeholder which will be replaced with the task name.

```python
setup(app, darq, logs_url="https://mylogserver.com/taskname=${taskName}")
```

#### Kibana url example

If you have kibana, you can use the following url:

In this url, `task_name` is a field name and `${taskName}` will be replaced with the task name value.

```
https://kibana.corp/app/discover#/?_g=(time:(from:now-15m,to:now))&_a=(filters:!((('$state':(store:appState),meta:(key:task_name,params:(query:'%22${taskName}%22')),query:(match_phrase:(task_name:’${taskName}')))))
```

## Examples

In order to run examples you need to install the dependencies:


```bash
cd examples
pdm install
```

And then run the server:

```bash
lets run-fastapi # or run-aiohttp
```

* [FastAPI example](examples/fastapi_server.py)
* [Aiohttp example](examples/aiohttp_server.py)

