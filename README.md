# darq-ui

## Installation

```bash
pip install darq-ui
```

Or with extra dependencies:

```bash
pip install darq-ui[aiohttp]
# or
pip install darq-ui[fastapi]
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

## Development

* pdm package manager - https://pdm.fming.dev/
* lets task runner https://lets-cli.org

### Run linters, formatters and other checks

```bash
$ pdm run ruff
$ pdm run ruff-fmt
$ pdm run mypy
```

### Changelog

When developing, add notes to CHANGELOG.md `Unreleased` section.

After we decided to release new version, we must rename `Unreleased` to new tag version and add new `Unreleased` section.

## Publishing

`darq-ui` supports semver versioning.

* Update the version number in the `src/darq_ui/__init__.py` file.
* Update the changelog in the `CHANGELOG.md` file.
* Merge changes into master.
* Create a tag `git tag -a v0.0.X -m 'your tag message'`.

All of the above steps can be done with the following command:
```bash
lets release <version> -m 'your release message'
```

This command will update the version in the `__init__.py` file, update the changelog, create a tag and push it to the repository.

When new tag pushed, new release action on GitHub will publish new package to pypi.
