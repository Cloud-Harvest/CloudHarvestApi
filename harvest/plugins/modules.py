from importlib import util
from typing import Any
from subprocess import run
from logging import getLogger

logger = getLogger('harvest')


class Module:
    def __init__(self, path: str, module: Any):
        self.path = path
        self.module = module


class Plugin:
    def __init__(self, source: str, label: str = None):
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

    def activate(self):
        self._clone()
        self._install_python_requirements()
        self._run_setup_bash()
        self._load()

        return self
        
    def _clone(self):
        from os.path import exists, join
        from plugins.registry import PluginRegistry
        from plugins.exceptions import PluginImportException

        args = ['git',
                'clone',
                '--recurse-submodules',
                '--single-branch']

        if self._label:
            args.append(f'--branch={self._label}')

        self.name = self._source.split('/')[-1].replace('.git', '')

        self._destination = join(PluginRegistry.path, self.name)

        logger.debug(f'clone: {self._source} -> {self._destination}')

        if exists(self._destination):
            logger.debug(f'{self.name}: -> {self._destination}')

        else:
            logger.debug(f'{self.name}: -> {self._destination}')
            r = run(args=args + [self._source, self._destination])

            self.status = r.returncode

            if r.returncode == 0:
                self.message = 'OK'
                logger.debug(f'clone: OK: {self._source} -> {self._destination}')

            else:
                raise PluginImportException(f'error when attempting to retrieve {self._source}')

        # check for a harvest plugin meta.yaml file
        # contains keys: name, author, url, and version
        meta_path = join(self._destination, 'meta.yaml')

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

        # update the system path with the plugin path (if it is not already present)
        import sys
        if self._destination not in sys.path:
            sys.path.append(self._destination)

        return self

    def _install_python_requirements(self):
        from plugins.exceptions import PluginImportException
        from os.path import exists, join
        requirements = join(self._destination, 'requirements.txt')

        if exists(requirements):
            logger.info(f'{self.name}: install python packages')
            process = run(args=['pip', 'install', '-r', requirements])

            if process.returncode != 0:
                raise PluginImportException(f'{self.name}: errors while install python packages')

        else:
            logger.debug(f'{self.name}: no python requirements found')

    def _run_setup_bash(self):
        from plugins.exceptions import PluginImportException
        from platform import platform
        os_filename = 'setup.bat' if 'windows' in platform().lower() else 'setup.sh'

        from os.path import exists, join
        setup_file = join(self._destination, os_filename)

        if exists(setup_file):
            logger.info(f'{self.name}: run {os_filename}')
            process = run(args=[setup_file])

            if process.returncode != 0:
                raise PluginImportException(f'{self.name}: errors while running setup.sh')

        else:
            logger.debug(f'{self.name}: no setup.sh found')

    def _load(self):
        from plugins.exceptions import PluginImportException
        from os import listdir
        from os.path import join

        # originally based on
        # https://gist.github.com/dorneanu/cce1cd6711969d581873a88e0257e312

        try:
            for filename in listdir(self._destination):
                if filename.endswith('.py') and not filename.startswith('.') and not filename.startswith('__'):
                    f = join(self._destination, filename)

                    name = filename[0:-3]
                    spec = util.spec_from_file_location(name, f)
                    module = util.module_from_spec(spec)
                    spec.loader.exec_module(module)

                    self.modules.append(Module(path=join(self._destination, filename), module=module))

        except ModuleNotFoundError as ex:
            raise PluginImportException(*ex.args)

        return self
