from typing import List, Dict
from subprocess import run
from logging import getLogger

logger = getLogger('harvest')


class PluginRegistry:
    path = None
    plugins = []
    repos: List[Dict] = []
    objects = {}

    @staticmethod
    def initialize(path: str, repos: List[Dict[str, str]]):
        # create module_path if it does not exist
        from pathlib import Path
        p = Path(path).expanduser().absolute()
        p.mkdir(parents=True, exist_ok=True)

        # set the path to the global Plugin registry
        PluginRegistry.path = str(p)
        PluginRegistry.repos = repos

        return PluginRegistry

    @staticmethod
    def load():
        from plugins.modules import Plugin
        # check if git is installed
        if run(args=['git', '--version']).returncode != 0:
            raise FileNotFoundError('git was not found in the path',
                                    'git is required to retrieve remote modules')

        PluginRegistry.plugins = [Plugin(**repo).activate() for repo in PluginRegistry.repos]

        return PluginRegistry

    @staticmethod
    def meta():
        return [
            {k: v for k, v in dict(vars(plugin)).items() if isinstance(v, str) and not str(k).startswith('_')}
            for plugin in PluginRegistry.plugins
        ]