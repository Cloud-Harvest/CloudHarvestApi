from logging import getLogger
from typing import Any

logger = getLogger('harvest')


class PluginRegistry:
    """
    The PluginRegistry class is responsible for managing plugins in the application. It provides methods to install, initialize, and retrieve plugins.

    Attributes:
        classes (dict): A dictionary to store uninstantiated classes of the plugins.
        plugins (dict): A dictionary to store the plugins, populated from HarvestConfiguration.plugins.
        modules (dict): A dictionary to store loaded modules.
    """

    classes = {}
    plugins = {}
    modules = {}

    @staticmethod
    def install():
        """
        Installs all plugins in PluginRegistry.plugins. Once all plugins are installed, they are initialized.
        """

        if not PluginRegistry.plugins:
            logger.warning('No plugins to install.')
            return

        from subprocess import run, PIPE

        args = ['pip', 'install'] + [f'git+{url}@{branch}' for url, branch in PluginRegistry.plugins.items()]

        logger.debug(f'Installing plugins: {" ".join(args)}')

        process = run(args=args, stdout=PIPE, stderr=PIPE)

        if process.returncode != 0:
            logger.error(f'Plugin installation failed with error code {process.returncode}')
            logger.error(f'Plugin installation output:' + process.stdout.decode('utf-8') + process.stderr.decode('utf-8'))

        else:
            logger.debug(f'Plugin installation output:' + process.stdout.decode('utf-8') + process.stderr.decode('utf-8'))

            PluginRegistry.initialize()

    @staticmethod
    def initialize():
        """
        Initializes all plugins in the PluginRegistry. It imports all packages in the site-packages directory that
        start with 'CloudHarvest' and are not already imported. Then, it gets all classes within the module.
        """

        import os
        import glob
        import site
        import sys
        import importlib

        # Get the path of the site-packages directory
        site_packages_path = site.getsitepackages()[0]

        # Create a pattern for directories starting with 'CloudHarvest'
        pattern = os.path.join(site_packages_path, 'CloudHarvest*')

        # Iterate over all directories in the site-packages directory that match the pattern
        for directory in glob.glob(pattern):
            # Get the package name from the directory path
            package_name = os.path.basename(directory)

            # Check if the package is already imported
            if package_name not in sys.modules and 'dist-info' not in package_name:
                # If the package is not already imported, import it
                PluginRegistry.modules[package_name] = importlib.import_module(package_name)

                # Get all classes within the module
                PluginRegistry.classes[package_name] = PluginRegistry._get_all_classes(PluginRegistry.modules[package_name])

        return PluginRegistry

    @staticmethod
    def get_class_by_name(name: str) -> Any:
        """
        Retrieves a class from the PluginRegistry by its name.

        Args:
            name (str): The name of the class.

        Returns:
            The class if it exists in the PluginRegistry; otherwise, None.
        """

        for package_name, classes in PluginRegistry.classes.items():
            for cls_name, cls in classes.items():
                if cls_name == name:
                    return cls

    @staticmethod
    def get_class_by_subtype(subtype: Any) -> Any:
        """
        Retrieves a class from the PluginRegistry by its subtype.

        Args:
            subtype (Any): The subtype of the class.

        Returns:
            The class if it exists in the PluginRegistry; otherwise, None.
        """

        for package_name, classes in PluginRegistry.classes.items():
            for cls_name, cls in classes.items():
                if issubclass(cls, subtype):
                    return cls

    @staticmethod
    def _get_all_classes(package):
        """
        Retrieves all classes from a package.

        Args:
            package: The package to retrieve classes from.

        Returns:
            A dictionary of classes in the package.
        """

        import pkgutil
        import importlib
        import inspect

        classes = {}
        for _, module_name, _ in pkgutil.walk_packages(package.__path__, package.__name__ + '.'):
            module = importlib.import_module(module_name)
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj) and package.__name__ in obj.__module__:
                    classes[name] = obj

        return classes
