from api.launch import init_app
from configuration import HarvestConfiguration

app = init_app()

if __name__ == '__main__':
    app.run(**HarvestConfiguration.api)
