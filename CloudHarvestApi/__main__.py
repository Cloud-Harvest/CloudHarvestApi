"""
Entrypoint for the CloudHarvestApi
"""
from CloudHarvestApi.startup import (
    load_configuration_from_file,
    load_logging,
    load_silos,
    start_node_heartbeat
)
from CloudHarvestCorePluginManager import Registry, register_all
from CloudHarvestCorePluginManager.plugins import generate_plugins_file, install_plugins
from CloudHarvestCoreTasks.dataset import WalkableDict
from CloudHarvestCoreTasks.environment import Environment
from argparse import ArgumentParser, Namespace
from flask import Flask
from os import getpid

# Imports objects which need to be registered by the CloudHarvestCorePluginManager
from CloudHarvestApi.__register__ import *

# The flask server object
app = Flask('CloudHarvestApi')

if __name__ == '__main__':
    parser = ArgumentParser(description='CloudHarvestApi')
    debug_group = parser.add_argument_group('DEBUG OPTIONS', description='Options when running the application in '
                                                                         'debug mode. None of the options presented here '
                                                                         'are required if the application is running using '
                                                                         'a WSGI server, such as gunicorn.')
    debug_group.add_argument('--host', type=str, default='127.0.0.1', help='Host address')
    debug_group.add_argument('--port', type=int, default=8000, help='Port number')
    debug_group.add_argument('--pemfile', type=str, default='./app/harvest-self-signed.pem', help='Use PEM file for SSL')
    debug_group.add_argument('--debug', action='store_true', help='Enable debug mode')

    args = parser.parse_args()

else:
    # If the script is not run as the main module, collect the variables from the environment
    from os import environ
    args = Namespace(host=environ.get('CLOUDHARVESTAPI_HOST'),
                     port=int(environ.get('CLOUDHARVESTAPI_PORT')),
                     pemfile=environ.get('CLOUDHARVESTAPI_PEMFILE'),
                     debug=False)

# Load the configuration
config = WalkableDict(**load_configuration_from_file())
config['api']['connection'] = vars(args)
config['api']['pid'] = getpid()

# Makes the configuration available throughout the app
Environment.merge(config)

# Install plugins
generate_plugins_file(config.get('plugins') or {})
install_plugins(quiet=args.debug or config.walk('api.logging.quiet'))

# Find all plugins and register their objects and templates
register_all()

# Register the blueprints from this app and all plugins
with app.app_context():
    [
        app.register_blueprint(api_blueprint)
        for api_blueprint in Registry.find(result_key='instances',
                                           category='blueprint',
                                           name='api')
        if api_blueprint is not None
    ]


# Configure logging
logger = load_logging(log_destination=config.walk('api.logging.location'),
                      log_level=config.walk('api.logging.level'),
                      quiet=config.walk('api.logging.quiet'))

logger.info('Api configuration loaded successfully.')

# Load the silos
load_silos(config.get('silos') or {})

# Start the node heartbeat
start_node_heartbeat(config)

logger.debug(app.url_map)
logger.info('Api node started.')

if args.debug:
    import ssl

    # Create SSL context using the PEM file
    ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_context.load_cert_chain(args.pemfile)

    # Start the Flask application
    app.run(host=args.host,port=args.port, ssl_context=ssl_context)
