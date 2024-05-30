from flask import Flask
from logging import getLogger
logger = getLogger('harvest')


def init_app():
    """Initialize the core application."""
    app = Flask('CloudHarvestApi', instance_relative_config=False)

    from configuration import HarvestConfiguration
    HarvestConfiguration.startup()

    with app.app_context():

        # Register the Blueprints
        from CloudHarvestCorePluginManager.registry import Registry
        from flask import Blueprint
        [
            app.register_blueprint(cache_blueprint)
            for cache_blueprint in Registry.find_instance(is_subclass_of=Blueprint, return_all_matching=True)
            if cache_blueprint is not None
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
