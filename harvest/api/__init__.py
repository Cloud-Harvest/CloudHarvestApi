import configuration
from flask import Flask

# Globally accessible libraries
from .reports import reporting_bp


def init_app():
    """Initialize the core application."""
    app = Flask('cloud-harvest-api', instance_relative_config=False)
    app.config.from_mapping(configuration.api_configuration.get('api', {}))

    with app.app_context():
        # Include our Routes

        # Register Blueprints
        app.register_blueprint(reporting_bp)

        # register Blueprints from the PluginRegistry
        from plugins.registry import PluginRegistry
        from flask.blueprints import Blueprint
        [app.register_blueprint(blueprint) for blueprint in PluginRegistry.of_type(Blueprint)]

        return app
