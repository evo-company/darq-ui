# darq-ui

## TODO

* [ ] Embed current interal UI based on ANTD and distribute it via pypi
* [ ] Http api that can be exposed via midlleware ? (Adapt internal graphql mutations)
* [ ] FastApi integration ?
* [ ] Aiohttp integration ?

The idea is to have a simple integration of a darq ui into project. 
Something like:

```bash
pip install darq-ui
```

```python
from aiohttp import web
from darq_ui.integration.aiohttp import setup

app = web.Application()

# expose /darq endpoint to load the ui
# expose /darq/api endpoint to interact with the darq (load tasks, run tasks)
setup(app)  
```
