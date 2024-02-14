from typing import List, Dict
from subprocess import run
from logging import getLogger

logger = getLogger('harvest')


class PluginRegistry:
    path = None
    plugins = []
    objects = {}

    def __init__(self, path: str, repos: List[Dict[str, str]]):
        # create module_path if it does not exist
        from pathlib import Path
        p = Path(path).expanduser().absolute()
        p.mkdir(parents=True, exist_ok=True)

        # set the path to the global Plugin registry
        PluginRegistry.path = str(p)
        self.repos = repos

    def initialize_repositories(self):
        from .modules import Plugin
        # check if git is installed
        if run(args=['git', '--version']).returncode != 0:
            raise FileNotFoundError('git was not found in the path',
                                    'git is required to retrieve remote modules')

        plugins = [Plugin(**repo) for repo in self.repos]

        for plugin in plugins:
            plugin.clone()
            plugin.install_python_requirements()
            plugin.run_setup_bash()
            plugin.load()

        return self
