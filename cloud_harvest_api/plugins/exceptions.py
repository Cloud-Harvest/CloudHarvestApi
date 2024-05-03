from core.tasks import BaseHarvestException


class PluginImportException(BaseHarvestException):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
