from api.launch import init_app
from startup import HarvestConfiguration

app = init_app()

if __name__ == '__main__':
    app.run(**HarvestConfiguration.api)
