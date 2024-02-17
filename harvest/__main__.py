import configuration
from argparse import ArgumentParser
from rich_argparse import RawTextRichHelpFormatter
from cache.connection import HarvestCacheConnection
from cache.heartbeat import HarvestCacheHeartBeatThread
from plugins.registry import PluginRegistry
from flask import Flask, jsonify, Response

# define the application
app = Flask('cloud-harvest-api')

parser = ArgumentParser(formatter_class=RawTextRichHelpFormatter)
parser.add_argument('--purge-plugins',
                    action='store_true',
                    help='Delete the existing plugin directory. Useful for upgrading plugins.')

log_argument_group = parser.add_argument_group('Logging')
log_argument_group.add_argument('--level',
                                choices=['debug', 'info', 'warning', 'error', 'critical'],
                                help='Set the terminal log level.\n'
                                'Note that the log file is always set to `debug`.')
log_argument_group.add_argument('--quiet',
                                action='store_true',
                                help='Suppress terminal output.\n'
                                     'Continues to `debug` write to the log file.')

args = dict(vars(parser.parse_args()))

# load configurations and begin startup sequence
api_configuration = configuration.load_configuration_files()
logger = configuration.load_logger(**api_configuration.get('logging', {}) | args)

# load modules
PluginRegistry.initialize(**(api_configuration['modules'] | args)).load()

# load reports from file system
reports = configuration.load_reports('./harvest', api_configuration.get('modules', {}).get('path'))

# test backend connection
cache = HarvestCacheConnection(**api_configuration['cache']['connection'])

# begin heartbeat thread
HarvestCacheHeartBeatThread(cache=cache, version=api_configuration['version'])

logger.info('api startup complete')


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
    # local api reports
    result = [
        {
            'name': k,
            'description': v.get('description', 'no description')
         }
        for k, v in reports.items()
    ]

    # get a list of unique data collector nodes from the database (sort DESC by version so we get the latest)

    # pull the available reports from those collectors

    return jsonify(result)


@app.errorhandler(404)
def not_found():
    return "404 - not found"


if __name__ == '__main__':
    # start the webserver
    app.run(**api_configuration.get('api', {}))
