import configuration
from flask import Flask
from logging import getLogger
logger = getLogger('harvest')


def init_app():
    """Initialize the core application."""
    app = Flask('cloud-harvest-api', instance_relative_config=False)
    # app.config.from_mapping(configuration.api_configuration.get('api', {}))

    with app.app_context():
        # Register Blueprints
        load_blueprints(app=app, blueprint_dir='harvest/api/blueprints')

        # Register Blueprints added from plugins
        from plugins.registry import PluginRegistry
        from flask.blueprints import Blueprint
        [app.register_blueprint(blueprint) for blueprint in PluginRegistry.instantiated_of_type(Blueprint)]

        # Register Tasks
        from tasks.base import BaseTask, BaseTaskChain
        load_subclasses('harvest/**/tasks.py', BaseTask, BaseTaskChain)

        # index the backend database
        try:
            from cache.connection import HarvestCacheConnection
            from cache.data import add_indexes
            from configuration import HarvestConfiguration
            add_indexes(client=HarvestCacheConnection(**HarvestConfiguration.cache['connection']),
                        indexes=HarvestConfiguration.cache.get('indexes'))
        except Exception as e:
            logger.error(f'Could not index the backend database: {e.args}')

        return app


def load_blueprints(app: Flask, blueprint_dir: str):
    """
    This function dynamically loads Flask blueprints from a specified directory.

    Parameters:
    app (Flask): The Flask application instance to which the blueprints will be registered.
    blueprint_dir (str): The directory path where the blueprints are located.

    The function iterates over all the directories in the given path, and for each directory,
    it looks for a 'routes.py' file. If found, it imports the module and registers any Flask
    blueprints it finds to the provided Flask application.

    The function also logs the name of each loaded blueprint for debugging purposes.
    """

    from os import listdir
    from os.path import isfile, join
    from importlib import import_module
    from flask import Blueprint

    for blueprint in listdir(blueprint_dir):
        if isfile(join(blueprint_dir, blueprint)):
            continue

        for filename in listdir(join(blueprint_dir, blueprint)):
            if filename == 'routes.py':
                module_name = filename[:-3]  # remove .py extension
                module_path = join(blueprint_dir, blueprint).replace('/', '.') + '.' + module_name
                module_path = '.'.join(module_path.split('.')[1:])  # remove leading 'harvest' (or equivalent)

                logger.info(f'Loading module: {module_path}')

                module = import_module(module_path)
                for item in dir(module):
                    obj = getattr(module, item)
                    if isinstance(obj, Blueprint):
                        app.register_blueprint(obj)
                        logger.debug(f'Loaded blueprint: {obj.name}')


def load_subclasses(pathname: str = 'harvest', *subclass_types):
    import inspect
    from tasks.base import BaseTask, BaseTaskChain

    subclasses = []

    from glob import glob
    for module in glob(pathname, recursive=True):
        module = module.replace('/', '.').replace('\\', '.').replace('.py', '')
        module = module.split('harvest.')[1]
        module = __import__(module, fromlist=[''])

        for name, obj in inspect.getmembers(module):
            if inspect.isclass(obj) and any([issubclass(obj, base_class) for base_class in subclass_types]):
                subclasses.append(obj)

    logger.debug('Loaded subclasses: ' + ', '.join([subclass.__name__ for subclass in subclasses]))
    return subclasses
