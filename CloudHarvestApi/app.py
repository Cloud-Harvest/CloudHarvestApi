from flask.json.provider import DefaultJSONProvider


class UpdatedJSONProvider(DefaultJSONProvider):
    # adopted from https://stackoverflow.com/a/74618781
    def default(self, o):
        if isinstance(o, (date, datetime)):
            return o.strftime("%Y-%m-%d %H:%M:%S.%f")

        return super().default(o)


class CloudHarvestApi:
    app = None
    config = {}

    @staticmethod
    def run(**kwargs):
        CloudHarvestApi.app.json = UpdatedJSONProvider(CloudHarvestApi.app)
        CloudHarvestApi.app.run(**kwargs)


if __name__ == '__main__':
    from datetime import datetime, date

    from api.launch import init_app
    from configuration import HarvestConfiguration
    from CloudHarvestCorePluginManager.registry import Registry

    # This __register__ module is necessary to load objects which should be placed in the
    # CloudHarvestCorePluginManager.registry; do not remove it
    from __register__ import *
    Registry.register_objects()

    CloudHarvestApi.app = init_app()
    CloudHarvestApi.run(**HarvestConfiguration.api)
