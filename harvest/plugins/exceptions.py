from base.exceptions import BaseHarvestException


class PluginImportException(BaseHarvestException):
    def __init__(self, *args):
        super().__init__(*args)
