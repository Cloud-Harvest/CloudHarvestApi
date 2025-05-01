"""
The `__register__.py` module is used to register objects that should be placed in the
`CloudHarvestCorePluginManager.registry.Registry`. Here, they are loaded via the `app.py` -> `api/launch.py`
startup process. Note that even though these modules do not appear to be used, they are necessary to register both
Tasks and Blueprints for the Flask application.
"""

# Register Blueprints
from CloudHarvestApi.blueprints import *
