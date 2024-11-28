from flask import Blueprint
from CloudHarvestCorePluginManager.decorators import register_definition
from logging import getLogger

logger = getLogger('harvest')

# Import the CloudHarvestApi to make it available to
from ..configuration import HarvestConfiguration


@register_definition(category='api_blueprint', name='harvest_blueprint', register_instances=True)
class HarvestApiBlueprint(Blueprint):
    def __init__(self, *args, **kwargs):
        logger.info(f'Initializing Blueprint: {args[0]}')

        super().__init__(*args, **kwargs)

