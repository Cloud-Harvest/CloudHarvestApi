from cache import HarvestCacheConnection
from flask import Flask

# load configurations and begin startup sequence
import startup
api_configuration = startup.load_configuration_files()
logger = startup.get_logger()


app = Flask(__name__)

# test backend connection
cache = {}
for node, host_configuration in api_configuration['cache'].items():
    c = HarvestCacheConnection(node=node, **host_configuration)
    cache[node] = c

    assert c.is_connected

# load modules
from modules import ModuleLoader, ModuleRegister


# start the webserver
app.run()


@app.route("/")
def default() -> str:
    return 'hello world'


@app.route("/reports/run")
def reports_run(name: str, matches: tuple = (), add: tuple = (), exclude: tuple = (), limit: int = None) -> dict:
    return {}


@app.route("/reports/list")
def reports_list() -> dict:
    return {}
