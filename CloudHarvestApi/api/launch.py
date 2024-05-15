from flask import Flask
from logging import getLogger
logger = getLogger('harvest')


def init_app():
    """Initialize the core application."""
    app = Flask('CloudHarvestApi', instance_relative_config=False)

    from configuration import HarvestConfiguration
    HarvestConfiguration.startup()

    with app.app_context():
        from CloudHarvestCorePluginManager import PluginRegistry

        # Add this program's Task classes to the PluginRegistry
        PluginRegistry.register_all_classes_by_path('./CloudHarvestApi/cache/')

        # Register the instantiated classes in the blueprints directory
        PluginRegistry.register_instantiated_classes_by_path('./CloudHarvestApi/api/blueprints')

        # Register Blueprints added from plugins
        from flask.blueprints import Blueprint
        [
            app.register_blueprint(blueprint)
            for blueprint in PluginRegistry.find_classes(is_instance_of=Blueprint,
                                                         return_all_matching=True,
                                                         return_type='instantiated') or []
            if blueprint is not None
        ]

        # index the backend database
        try:
            # TODO: this should be a thread service which is passed through a quorum system
            from cache.connection import HarvestCacheConnection
            from cache.data import add_indexes
            from configuration import HarvestConfiguration
            add_indexes(client=HarvestCacheConnection(**HarvestConfiguration.cache),
                        indexes=HarvestConfiguration.indexes)

        except Exception as e:
            logger.error(f'Could not index the backend database: {e.args}')

        return app
