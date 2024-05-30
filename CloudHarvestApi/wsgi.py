class CloudHarvestApi:
    app = None

    @staticmethod
    def run(**kwargs):
        CloudHarvestApi.app.run(**kwargs)


if __name__ == '__main__':
    from api.launch import init_app
    from configuration import HarvestConfiguration
    from CloudHarvestCorePluginManager.registry import Registry

    # This __register__ module is necessary to load objects which should be placed in the
    # CloudHarvestCorePluginManager.registry; do not remove it
    from __register__ import *
    Registry.register_objects()

    CloudHarvestApi.app = init_app()
    CloudHarvestApi.run(**HarvestConfiguration.api)
