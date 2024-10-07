"""
This module is the entry point for the CloudHarvestApi application.
"""

from flask import Flask
from logging import getLogger
logger = getLogger('harvest')


def init_app():
    """Initialize the core application."""
    app = Flask('CloudHarvestApi')

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
            from CloudHarvestCoreTasks.silos.persistent import add_indexes
            add_indexes(indexes=HarvestConfiguration.indexes)

        except Exception as e:
            logger.error(f'Could not index the backend database: {e.args}')

        return app
