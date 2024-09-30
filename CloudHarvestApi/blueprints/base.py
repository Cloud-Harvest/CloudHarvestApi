from flask import Blueprint
from CloudHarvestCorePluginManager.decorators import register_instance
from logging import getLogger

logger = getLogger('harvest')


@register_instance
class HarvestBlueprint(Blueprint):
    def __init__(self, *args, **kwargs):
        logger.info(f'Initializing Blueprint: {args[0]}')

        super().__init__(*args, **kwargs)

