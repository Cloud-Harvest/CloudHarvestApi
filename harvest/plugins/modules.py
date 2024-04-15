from typing import Any, AnyStr, List, Tuple
from logging import getLogger

logger = getLogger('harvest')


class Plugin:
    def __init__(self, source: str, label: str = None):
        self._source = source
        self._label = label

        self._destination = None

        self.name = None
        self.author = None
        self.url = None
        self.version = None

        self.objects = []
        self.status = None
        self.message = None

    def activate(self):
        self._clone()
        self._install_python_requirements()
        self._run_setup_bash()
        self._load()

        logger.debug(f'{self.name}: module initialization complete')

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

            process = self._run(arguments=args + [self._source, self._destination])

            self.status = process[0]

            if self.status == 0:
                self.message = 'OK'
                logger.debug(f'clone: OK: {self._source} -> {self._destination}')

            else:
                raise PluginImportException(
                    f'{self.name}: {self._source}, {str(process[0])}',
                    process[1],
                    process[2]
                )
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
            process = self._run(arguments=['pip', 'install', '-r', requirements])

            if process[0] != 0:
                raise PluginImportException(
                    f'{self.name}: errors while install python packages',
                    process[1],
                    process[2]
                )
        else:
            logger.debug(f'{self.name}: no python requirements found')

        return self

    def _run_setup_bash(self):
        from plugins.exceptions import PluginImportException
        from platform import platform
        os_filename = 'setup.bat' if 'windows' in platform().lower() else 'setup.sh'

        from os.path import exists, join
        setup_file = join(self._destination, os_filename)

        if exists(setup_file):
            logger.info(f'{self.name}: run {os_filename}')
            process = self._run(arguments=[setup_file])

            if process[0] != 0:
                raise PluginImportException(f'{self.name}: errors while running setup.sh',
                                            process[1],
                                            process[2])

        else:
            logger.debug(f'{self.name}: no setup.sh found')

        logger.debug(f'{self.name}: setup complete')

        return self

    def _load(self):
        import pkgutil
        import sys
        from importlib import import_module
        from inspect import getmembers, isclass
        from os.path import basename, join

        sys.path.insert(0, join(self._destination))

        package_name = basename(self._destination)
        package = __import__(package_name, fromlist=[''])

        # Iterate over all the modules in the package
        for importer, module_name, _ in pkgutil.walk_packages(package.__path__, package_name + '.'):
            # Import the module
            try:
                module = import_module(module_name)

                objects = [
                    (m[0], m[1], package_name)
                    for m in getmembers(module)
                ]

                # Get all the classes
                self.objects.extend(objects)

                logger.debug(f'{self.name}: module loaded')

            except ModuleNotFoundError:
                from traceback import format_exc
                logger.debug(f'{self.name}: could not import {module_name}\n{format_exc()}')
                continue

        return self

    @staticmethod
    def _run(arguments: List[AnyStr]) -> Tuple[int, AnyStr, AnyStr]:
        from subprocess import run, PIPE
        process = run(args=arguments, stdout=PIPE, stderr=PIPE)

        return (
            process.returncode,
            ' '.join(arguments),
            '\n'.join([bytes(s).decode('utf8') for s in process.stdout + process.stderr])
        )
