"""
This module is the entry point for the CloudHarvestApi application.
"""

from flask import Flask
from flask.json.provider import DefaultJSONProvider
from logging import getLogger
from datetime import datetime, date

logger = getLogger('harvest')


class CloudHarvestApi:
    """
    This class is the entry point for the CloudHarvestApi application.
    """

    app = None

    @staticmethod
    def run(**kwargs):
        """
        This method runs the CloudHarvestApi application.
        """

        CloudHarvestApi.app.json = UpdatedJSONProvider(CloudHarvestApi.app)
        CloudHarvestApi.app.run(**kwargs)


class UpdatedJSONProvider(DefaultJSONProvider):
    # adopted from https://stackoverflow.com/a/74618781
    def default(self, o):
        if isinstance(o, (date, datetime)):
            return o.strftime("%Y-%m-%d %H:%M:%S.%f")

        return super().default(o)


def init_app():
    """Initialize the core application."""
    app = Flask('CloudHarvestApi')

    from configuration import HarvestConfiguration
    HarvestConfiguration.startup()

    with app.app_context():

        # Register the Blueprints
        from CloudHarvestCorePluginManager.registry import Registry
        [
            app.register_blueprint(api_blueprint)
            for api_blueprint in Registry.find(result_key='instances', name='blueprint')
            if api_blueprint is not None
        ]

        # index the backend database
        try:
            from CloudHarvestCoreTasks.silos.persistent import add_indexes
            add_indexes(indexes=HarvestConfiguration.indexes)

        except Exception as e:
            logger.error(f'Could not index the backend database: {e.args}')

        return app


if __name__ == '__main__':
    from configuration import HarvestConfiguration
    from CloudHarvestCorePluginManager.functions import register_objects

    # This __register__ module is necessary to load objects which should be placed in the
    # CloudHarvestCorePluginManager.registry; do not remove it
    from __register__ import *
    register_objects()

    CloudHarvestApi.app = init_app()
    CloudHarvestApi.run(**HarvestConfiguration.api)
