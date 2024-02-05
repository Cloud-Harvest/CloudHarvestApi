import configuration
from cache.connection import HarvestCacheConnection
from cache.heartbeat import HarvestCacheHeartBeatThread
from flask import Flask, jsonify, Response

# define the application
app = Flask(__name__)

# load configurations and begin startup sequence
api_configuration = configuration.load_configuration_files()
logger = configuration.load_logger(**api_configuration.get('logging', {}))

reports = configuration.load_reports()

# test backend connection
cache = HarvestCacheConnection(**api_configuration['cache']['connection'])

# begin heartbeat thread
HarvestCacheHeartBeatThread(cache=cache, version=api_configuration['version'])


@app.route("/")
def default() -> str:
    return 'Harvest API Server'


@app.route("/reports/run")
def reports_run(name: str, match: list = None, add: list = None, limit: int = None, order: list = None, **kwargs) -> Response:
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
def reports_list() -> Response:
    result = [{'name': k, 'description': v['description']} for k, v in reports.items()]

    return jsonify(result)


@app.errorhandler(404)
def not_found():
    return "404 - not found"


if __name__ == '__main__':
    # start the webserver
    app.run(**api_configuration.get('api', {}))
