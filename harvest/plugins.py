from base.exceptions import PluginImportException
from importlib import util
from typing import Any, List, Dict
from subprocess import run

from logging import getLogger

logger = getLogger('harvest')


class PluginRegistry:
    path = None
    plugins = []

    def __init__(self, path: str, repos: List[Dict[str, str]]):

        # create module_path if it does not exist
        from pathlib import Path
        p = Path(path).expanduser().absolute()
        p.mkdir(parents=True, exist_ok=True)

        PluginRegistry.path = str(p)
        self.repos = repos

    def initialize_repositories(self):
        # check if git is installed
        if run(args=['git', '--version']).returncode != 0:
            raise FileNotFoundError('git was not found in the path',
                                    'git is required to retrieve remote modules')

        plugins = [Plugin(**repo) for repo in self.repos]

        for plugin in plugins:
            plugin.clone()
            plugin.load()

        return self


class Module:
    def __init__(self, path: str, module: Any):
        self.path = path
        self.module = module


class Plugin:
    def __init__(self, source: str, label: str = None):
        from os.path import abspath, expanduser

        self._source = source
        self._label = label

        self._destination = None

        self.name = None
        self.author = None
        self.url = None
        self.version = None

        self.modules = []
        self.status = None
        self.message = None

    def clone(self):
        from os.path import exists, join

        args = ['git',
                'clone',
                '--recurse-submodules',
                '--single-branch']

        if self._label:
            args.append(f'--branch={self._label}')

        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as td:
            logger.debug(f'clone: {self._source} -> {td}')

            r = run(args=args + [self._source, td])

            self.status = r.returncode

            if r.returncode == 0:
                self.message = 'OK'
                logger.debug(f'clone: OK: {self._source} -> {td}')

            else:
                raise PluginImportException('error when attempting to retrieve {self._source}')

            # check for a harvest plugin meta.yaml file
            # contains keys: name, author, url, and version
            meta_path = join(td, 'meta.yaml')

            if exists(meta_path):
                from yaml import safe_load
                with open(meta_path) as plugin_meta_file:
                    plugin_meta = safe_load(plugin_meta_file)

                    metadata_required_fields = ('name', 'author', 'url', 'version')

                    if not all(s in plugin_meta.keys() for s in metadata_required_fields):
                        raise PluginImportException('plugin metadata must contain all of the following fields:'
                                                    f' {str(metadata_required_fields)}')

                    [setattr(self, key, value)
                     for key, value in plugin_meta.items()]

            else:
                raise PluginImportException(f'clone: {self._source}: plugins must contain a meta.yaml'
                                            f' file in the root repository directory')

            from shutil import copytree, ignore_patterns
            from os.path import sep
            self._destination = join(PluginRegistry.path, self.name)
            logger.debug(f'{self.name}: {td} -> {self._destination}')
            copytree(src=td, dst=self._destination, dirs_exist_ok=True, ignore=ignore_patterns(f'.git*'))

        return self

    def load(self):
        from os import listdir
        from os.path import join

        # originally based on
        # https://gist.github.com/dorneanu/cce1cd6711969d581873a88e0257e312

        for filename in listdir(self._destination):
            if filename.endswith('.py') and not filename.startswith('.') and not filename.startswith('__'):
                f = join(self._destination, filename)

                name = filename[0:-3]
                spec = util.spec_from_file_location(name, f)
                module = util.module_from_spec(spec)
                spec.loader.exec_module(module)

                self.modules.append(Module(path=join(self._destination, filename), module=module))

        PluginRegistry.loaded_plugins = self

        return self
