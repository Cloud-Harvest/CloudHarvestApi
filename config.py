"""
Cloud Harvest API Configuration Tool

This script assists in setting up the Cloud Harvest API by generating a configuration file (`harvest.json`)
based on user input. It also provides options to reset the configuration to defaults and to add plugins.

Functions:
    main(reset: bool = False): Main function to run the configuration tool.
    ask(prompt: str, default: str = None, style: str = 'white', **kwargs) -> Any: Helper function to prompt user input.
    print_table(data: List[dict], keys: list = None, title:str = None): Helper function to print a list of dictionaries.

Usage:
    Run the script with the following command:
        python config.py
    To reset the configuration to defaults, use the `--reset` flag:
        python config.py --reset
"""
#!/bin/env python3

from rich.console import Console
from typing import Any, List

console = Console()


def main(reset: bool = False):
    """
    Main function to run the Cloud Harvest API Configuration Tool.

    Parameters:
    reset (bool): If True, resets the configuration file to defaults. Default is False.

    This function guides the user through a series of prompts to set up the configuration for the Cloud Harvest API.
    It updates or creates the `harvest.json` file with the provided settings.
    """

    from flatten_json import flatten, unflatten

    # Load the default configuration from the config.yaml file
    from yaml import load, FullLoader
    with open('./config.yaml') as config_file:
        ask_config = load(config_file, FullLoader)

    # Prints the welcome message and instructions
    console.print('\n'.join(['',
                             'Welcome to the Cloud Harvest API Configuration Tool!',
                             '',
                             'This tool will assist you in setting up your Cloud Harvest API.',
                             '* You can escape this process at any time with CTRL+C.',
                             '* You may also edit the file manually once it is created in ./app/harvest.json',
                             '* You can skip this process by copying an existing harvest.json to ./app/harvest.json',
                             '']))

    # Gathers the existing configurations if they exist
    from os.path import exists
    existing_config = {}
    if exists('./app/harvest.json') and reset is False:
        console.print('Loading existing configuration at `./app/harvest.json`', style='bold yellow')

        with open('./app/harvest.json') as existing_config_file_stream:
            from json import load
            try:
                existing_config = load(existing_config_file_stream)
            except Exception:
                existing_config = {}

    # Flatten the configurations so that we can easily merge them
    flat_existing_config = flatten(existing_config, separator='.')
    flat_ask_config = flatten(ask_config, separator='.')

    # A dictionary to store the results of the user prompts
    flat_results = {}

    # Helper function to ask for a part of the configuration
    def ask_part(name, **kwargs) -> Any:
        default = flat_existing_config.get(name) or flat_ask_config.get(f'{name}.default')

        kwargs['default'] = default
        kwargs['prompt'] = f'{name}: {kwargs["prompt"]}'
        result = ask(name=name, **kwargs)

        return result

    # Loop the configurations from ./config.yaml
    for root_key, root_value in ask_config.items():
        # We skip any keys that start with a period as they are considered hidden
        if root_key.startswith('.'):
            continue

        # Print a header when the root_key changes.
        console.print(f'\n{root_key.title()} Configuration', style='bold')
        if root_value.get('.description'):
            console.print(root_value['.description'], style='italic')

        # Ask the user if they would like to configure the root_key. If not, skip to the next root_key.
        do_root = ask(f'Would you like to configure {root_key.title()}?', choices=['y', 'n'], default='y').lower()

        # If the user chooses to configure the root_key, loop through the parts of the root_value
        if do_root == 'y':
            for part_key, part_value in root_value.items():
                # Skip hidden keys which begin with '.'
                if part_key.startswith('.'):
                    continue

                # Silos are nested beyond root_value
                if root_key == 'silos':
                    for silo_name, silo_config in part_value.items():
                        flat_key = f'{root_key}.{part_key}.{silo_name}'
                        flat_results[flat_key] = ask_part(name=flat_key, **silo_config)

                # Non-silo keys are not nested beyond root_value
                else:
                    flat_key = f'{root_key}.{part_key}'
                    flat_results[flat_key] = ask_part(name=flat_key, **part_value)

                # Add a new line after each part
                console.print()

    # Custom Silo Prompts
    # This section allows the user to add custom silos to the configuration.
    console.print('\nCustom Silos Configuration', style='bold')

    # A tuple of available engines to bse used as a data type backend. Presently, we only plan to support open source
    # engines, such as MongoDb or MySQL. This list can be expanded in the future as additional database backends are
    # supported. Another consideration when expanding this list should consider whether a proprietary engine's python
    # driver is available in the Python Package Index (PyPI). If it is not available in this easily distributed way,
    # we should consider how difficult it would be to install the driver in the containerized environment.
    valid_engines = ('mongodb', 'mysql', 'postgresql', 'redis')

    # Prompt the user if they would like to add custom silos
    do_custom_silos = ask('Would you like to add custom silos?', default='n').lower()

    # If the user chooses to add custom silos, prompt for the silo configuration
    if do_custom_silos == 'y':
        custom_silo_config = {
            'engine': {'prompt': 'Please enter the silo engine for {{name}}: ', 'choices': valid_engines},
            'host': {'prompt': 'Please enter the silo host IP address or hostname for {{name}}'},
            'port': {'prompt': 'Please enter the silo port for {{name}}'},
            'username': {'prompt': 'Please enter the silo username for {{name}}'},
            'password': {'prompt': 'Please enter the silo password for {{name}}: ', 'password': True},
            'database': {'prompt': 'Please enter the silo database for {{name}}'},
        }

        custom_silo_results = {}
        while True:
            try:
                silo_name = ask(name='silo.name', prompt='Please enter the silo name or leave empty to stop adding silos: ', default=None)
                if silo_name is None or silo_name == '':
                    break

                # Ask the user for responses to the key/value pairs in custom_silo_config
                custom_silo_result = {}
                for key, ask_config in custom_silo_config.items():
                    fq_key = f'silo.{silo_name}.{key}'

                    custom_silo_result.update({fq_key: ask(name=key, **ask_config)})

                # Special consideration for MongoDb authsource
                # As more database engines are supported, this section may need to be expanded to handle other
                # engine-specific configuration options.
                if custom_silo_result['engine'] == 'mongo':
                    custom_silo_result.update({f'silo.{silo_name}.authsource': ask(name=f'silo.{silo_name}.authsource', default='harvest', prompt='Please enter the silo authsource: ')})

                # Update the results for this entry with the custom_silo_result
                custom_silo_results.update(custom_silo_result)

            except KeyboardInterrupt:
                break

        # Merge the custom_silo_results with the flat_results
        flat_results.update(custom_silo_results)

    # Plugins Configuration
    # Prompt the user if they would like to instance plugins.
    do_plugins = ask('Would you like to add plugins?', default='n').lower()

    # If the user chooses to add plugins, prompt for the plugin configuration
    if do_plugins == 'y':
        plugin_config = {
            'url_or_package_name': {'prompt': 'Please enter the plugin package name or git URL for {{name}}.'},
            'branch': {'prompt': 'Please enter the version restriction (python) or tag name (git) for {{name}}', 'default': 'main'},
        }

        while True:
            try:
                # Ask the user for the plugin name. This field is arbitrary and can be any string, but it makes the
                # most sense to use the package name if the plugin is a Python package.
                plugin_name = ask(prompt='Please enter the plugin name or leave empty to stop adding plugins')
                if plugin_name is None or plugin_name == '':
                    break

                plugin_result = {}

                # Prompt the user for the plugin configuration as defined in the plugin_config dictionary
                for key, ask_config in plugin_config.items():
                    plugin_key = f'plugins.{plugin_name}.{key}'

                    # Update this plugin's configuration with the user's input
                    plugin_result.update({plugin_key: ask(name=key, **ask_config)})

                # Update the flat_results with the plugin_result
                flat_results.update(plugin_result)

            except KeyboardInterrupt:
                break

    # Convert the flat_results into a table where the key is the 'Name' and the value is the 'Value'
    table_data = [{'Name': k, 'Value': v} for k, v in flat_results.items()]
    print_table(data=table_data, keys=['Name', 'Value'], title='Configuration Preview')

    # Ask the user if they would like to save the configuration
    if ask('Would you like to save this configuration?', choices=['y', 'n'], default='n') == 'y':

        # Combine the new configuration with the existing configuration and unflatten the results. This allows us to
        # merge the existing configuration with the new configuration while maintaining the nested structure.
        results = unflatten(flat_existing_config | flat_results, separator='.')

        # Make sure the app directory exists
        if not exists('./app'):
            from os import mkdir
            mkdir('./app')

        # Dump the configuration to the file system
        from json import dumps
        with open('./app/harvest.json', 'w') as config_file_stream:
            config_file_stream.write(dumps(results, indent=4))

        # Notify the user the save operation completed
        console.print('Configuration saved to ./app/harvest.json', style='blue')

        # Write the plugins.txt file which allows us to install plugins via pip if plugins were provided.
        # Note that, for the purposes of plugin installation, the plugin entries stored in the plugins.txt file are
        # formatted as pip installable packages. The records stored in ./app/harvest.json are referential, but are
        # not used for installation. Only the contents of plugins.txt are used for installation.
        if results.get('plugins'):
            plugins_txt = []

            # Loop through the plugin configurations
            for plugin_name, plugin_config in results['plugins'].items():
                plugin_address = plugin_config.get('url_or_package_name')
                plugin_branch = plugin_config.get('branch')

                # Check if the plugin is a git URL or a Python package name
                if plugin_address.startswith('http') or plugin_address.endswith('.git'):
                    plugin_syntax = f'git+{plugin_address}@{plugin_branch or "main"}'

                # If the plugin does not have a URL, assume it is a Python package and use the package name
                else:
                    plugin_syntax = plugin_address + (f'@{plugin_branch}' if plugin_branch else '')

                # Append the plugin syntax to the plugins_txt list
                plugins_txt.append(plugin_syntax)

            # Write the plugins_txt list to the plugins.txt file
            with open('./app/plugins.txt', 'w') as plugins_file_stream:
                plugins_file_stream.writelines(plugins_txt)

            # Notify the user that the plugins were saved
            console.print('Plugins saved to ./app/plugins.txt', style='blue')

    # Print the outro message
    from rich.text import Text
    console.print(Text('You may now start the Harvest API using the following command: ', style='green') +
                  Text('./launch\n', style='blue') +
                  Text(' or ', style='green') +
                  Text('./launch --with-mongo\n', style='blue'))


def ask(prompt: str, name: str = None, choices: list = None, default: str = None, style: str = 'white', **kwargs) -> Any:
    """
    Helper function to prompt user input.
    Parameters
    ----------
    prompt (str): The prompt to display to the user.
    name (str, optional): The name to use in the prompt. Defaults to None.
    choices (list, optional): The list of choices to present to the user. Defaults to None.
    default (str, optional): The default value to use if the user does not provide input. Defaults to None.
    style (str, optional): The style to use for the prompt. Defaults to 'white'.
    kwargs (Any): Additional keyword arguments to pass to the prompt.

    Returns
    -------
    Any: The user input.
    """

    from rich.prompt import Prompt
    from rich.text import Text

    # Replaces the '{{name}}' placeholder in the prompt with the provided name
    if '{{name}}' in prompt and name:
        prompt = prompt.replace('{{name}}', name)

    # Executes the Prompt.ask function with the provided arguments
    result = Prompt.ask(prompt=Text(prompt, style=style),
                        choices=choices,
                        default=None if default is None else str(default),
                        **kwargs)

    # Determines the result type based on the default value and the user input
    if default is None and result is None:
        result = None

    elif default is not None and result is None:
        result = default

    elif default is None and result is not None:
        result = result

    else:
        result = type(default)(result)

    # Returns the user's input
    return result

def print_table(data: List[dict], keys: list = None, title:str = None):
    """
    Helper function to print a list of dictionaries as a table.

    Parameters
    data (List[dict]): The list of dictionaries to print as a table.
    keys (list, optional): The list of keys to use as columns. When not provided, the union of all keys in the data is used. Defaults to None.
    title (str, optional): The title of the table. Defaults to None.

    Returns
    No return value. Prints the table to the console.
    """

    from rich.table import Table
    from rich.box import SIMPLE

    # Create the table object using the SIMPLE box style.
    table = Table(box=SIMPLE, title=title)

    # Determine the columns and their order based on the keys provided or the union of all keys in the data.
    k = keys or list(set([k for d in data for k in d.keys()]))

    # Add the columns to the table.
    for key in k:
        table.add_column(key, overflow='fold')

    # Add the rows to the table, converting all values into string.
    for row in data:
        table.add_row(*[str(row.get(key, '')) for key in k])

    # Writes the table to the rich console.
    console.print(table)

if __name__ == '__main__':
    from rich_argparse import RichHelpFormatter
    from argparse import ArgumentParser

    parser = ArgumentParser(description='Cloud Harvest API Configuration Tool',
                            formatter_class=RichHelpFormatter)
    parser.add_argument('--reset', action='store_true', help='Reset the configuration file to defaults')

    args = parser.parse_args()

    main(reset=args.reset)
