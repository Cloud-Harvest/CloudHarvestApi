from typing import Any, List, Dict
from logging import getLogger

logger = getLogger('harvest')


class PluginRegistry:
    path = None
    plugins = []
    repos: List[Dict] = []
    objects = {}

    @staticmethod
    def initialize(path: str, repos: List[Dict[str, str]], purge_plugins: bool = False, **kwargs):
        from os.path import expanduser, exists
        # optionally purge the plugins directory -- useful for updating plugins
        if exists(expanduser(path)) and purge_plugins:
            logger.debug(f'purge plugin directory {path}')

            from shutil import rmtree
            rmtree(expanduser(path))

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
        from shutil import which
        git_binary = which('git')
        if git_binary:
            logger.debug(f'found git at: {git_binary}')
        else:
            raise FileNotFoundError('git was not found in the path',
                                    'git is required to retrieve remote modules')

        PluginRegistry.plugins = [Plugin(**repo).activate() for repo in PluginRegistry.repos]

        logger.info('plugin load complete')

        return PluginRegistry

    @staticmethod
    def meta() -> dict:
        results = {}

        for plugin in PluginRegistry.plugins:
            as_dict = dict(vars(plugin))

            results[as_dict['name']] = {
                k: v
                for k, v in as_dict.items()
                if isinstance(v, str) and not str(k).startswith('_')
            }

        return results

    @staticmethod
    def of_type(typeof: Any = None, name: str = None) -> List[Any]:
        """
        Returns plugin objects based on the type provided.
        """

        results = []

        for plugin in PluginRegistry.plugins:
            for o in plugin.objects:
                if typeof and isinstance(o[1], typeof):
                    results.append(o[1])

                if name and o[0] == name:
                    results.append(o[1])

        return results
