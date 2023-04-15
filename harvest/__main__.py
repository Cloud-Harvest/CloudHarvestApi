from flask import Flask

# load configurations and begin startup sequence
import startup
api_configuration = startup.load_configuration_files()
logger = startup.get_logger()


app = Flask(__name__)

app.run()


@app.route("/")
def default() -> str:
    return 'hello world'
