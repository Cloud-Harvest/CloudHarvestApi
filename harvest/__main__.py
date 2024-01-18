from cache.connection import HarvestCacheConnection
from flask import Flask, jsonify, Response

# load configurations and begin startup sequence
import configuration
api_configuration = configuration.load_configuration_files()
logger = configuration.load_logger(**api_configuration.get('logging', {}))

reports = configuration.load_reports()

# test backend connection
from cache.connection import HarvestCacheConnection
cache = HarvestCacheConnection(**api_configuration['cache']['connection'])

# load modules
from plugins import PluginRegistry
plugin_registry = PluginRegistry(**api_configuration['modules']).initialize_repositories()

# begin heartbeat thread
from cache.heartbeat import HarvestCacheHeartBeatThread
HarvestCacheHeartBeatThread(cache=cache, version=api_configuration['version'])

app = Flask(__name__)

# start the webserver
app.run(**api_configuration.get('api', {}))


@app.route("/")
def default() -> str:
    return 'hello world'


@app.route("/reports/run")
async def reports_run(name: str, match: list = None, add: list = None, limit: int = None, order: list = None, **kwargs) -> Response:
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

    return jsonify({})


@app.route("/reports/list", methods=['GET'])
async def reports_list() -> Response:
    return jsonify(list(reports.keys()))


@app.errorhandler(404)
def not_found():
    return "404 - not found"
