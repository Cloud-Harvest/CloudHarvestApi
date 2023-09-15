from cache import HarvestCacheConnection
from flask import Flask

# load configurations and begin startup sequence
import startup
api_configuration = startup.load_configuration_files()
logger = startup.load_logger(**api_configuration.get('logging', {}))


app = Flask(__name__)

# test backend connection
cache = startup.load_cache_connections(cache_config=api_configuration['cache']['hosts'])

# load modules
from plugins import PluginRegistry
plugin_registry = PluginRegistry(**api_configuration['modules']).initialize_repositories()

# start the webserver
app.run(**api_configuration.get('api', {}))


@app.route("/")
def default() -> str:
    return 'hello world'


@app.route("/reports/run")
async def reports_run(name: str, match: list = None, add: list = None, limit: int = None, order: list = None, **kwargs) -> dict:
    """
    execute a defined report and return the results
    :param name: the report to be executed
    :param match: matching logic
    :param add: appends extra fields to a report output
    :param limit: only return this many records
    :param order: sort results by these fields
    :return:
    """
    from reporting import Report
    with Report(**kwargs) as report:
        report.build()

    return {}


@app.route("/reports/list")
async def reports_list() -> dict:
    return {}
