class CloudHarvestApi:
    app = None

    @staticmethod
    def run(**kwargs):
        CloudHarvestApi.app.run(**kwargs)


if __name__ == '__main__':
    from api.launch import init_app
    from configuration import HarvestConfiguration
    CloudHarvestApi.app = init_app()
    CloudHarvestApi.run(**HarvestConfiguration.api)
