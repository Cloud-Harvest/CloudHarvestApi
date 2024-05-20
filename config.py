#!/bin/env python3

from typing import Any


def main(reset: bool = False):
    from rich.console import Console

    console = Console()

    defaults = {
        'api': {
            'host': '0.0.0.0',
            'port': 8000
        },
        'cache': {
            'host': 'harvest-mongo',
            'port': 27017,
            'username': 'harvest-api',
            'password': 'default-harvest-password',
            'authsource': 'harvest'         # tells MongoDB which database to authenticate against
        },
        'logging': {
            'level': 'debug',
            'location': './app/logs/'
        },
        'plugins': {}
    }

    console.print('\n'.join(['',
                             'Welcome to the Cloud Harvest API Configuration Tool!',
                             '',
                             'This tool will assist you in setting up your Cloud Harvest API.',
                             '* You can escape this process at any time with CTRL+C.',
                             '* You may also edit the file manually once it is created in ./app/harvest.json',
                             '* You can skip this process by copying an existing harvest.json to ./app/harvest.json',
                             '']))

    from os.path import exists

    if exists('./app/harvest.json') and reset is False:
        console.print('Loading existing configuration at `./app/harvest.json`', style='bold yellow')

        with open('./app/harvest.json', 'r') as existing_config_file_stream:
            from json import load
            existing_config = load(existing_config_file_stream)
            defaults.update(existing_config)

    try:
        defaults['api']['host'] = ask('Please enter the binding address for the API',
                                      default=defaults['api']['host'])
        defaults['api']['port'] = int(ask('Please enter the API port',
                                          default=defaults['api']['port']))
        defaults['cache']['host'] = ask('Please enter the cache host IP address or hostname',
                                        default=defaults['cache']['host'])
        defaults['cache']['port'] = int(ask('Please enter the cache port',
                                            default=defaults['cache']['port']))
        defaults['cache']['username'] = ask('Please enter the cache username',
                                            default=defaults['cache']['username'])
        defaults['cache']['password'] = ask('Please enter the cache password',
                                            default=defaults['cache']['password'],
                                            password=True)
        defaults['logging']['level'] = ask('Please enter the logging level',
                                           choices=['debug', 'info', 'warning', 'error', 'critical'],
                                           default=defaults['logging']['level'])
        defaults['logging']['location'] = ask('Please enter the logging location',
                                              default=defaults['logging']['location'])

        if defaults.get('plugins'):
            from rich.table import Table
            from rich.box import SIMPLE
            table = Table(title='Existing Plugins', box=SIMPLE)
            table.add_column('Plugin URL', overflow='fold')
            table.add_column('Branch', overflow='fold')

            for plugin_url, plugin_branch in defaults['plugins'].items():
                table.add_row(plugin_url, plugin_branch)

            console.print()
            console.print(table)

            keep_existing_plugins = ask('Would you like to keep the existing plugins?', default='y')
            if keep_existing_plugins.lower() == 'n':
                defaults['plugins'] = {}
                console.print('\nExisting plugins will not be carried over.', style='yellow')

        add_plugins = ask('Would you like to add a plugin at this time? (y/n)', default='n')

        if add_plugins.lower() == 'y':
            while True:
                plugin_url = ask('Please enter the plugin URL or leave empty to stop adding plugins: ')

                if plugin_url == '':
                    break

                elif not plugin_url.endswith('.git'):
                    console.print('Invalid plugin URL provided. Plugin URL must end with .git. Please try again',
                                  style='bold red')
                    continue

                plugin_branch = ask('Please enter the plugin branch', default='main')

                defaults['plugins'][plugin_url] = plugin_branch

    except KeyboardInterrupt:
        console.print('\nExiting...', style='bold red')
        exit(1)

    else:
        if not exists('./app'):
            from os import mkdir
            mkdir('./app')

        with open('./app/harvest.json', 'w') as config_file_stream:
            from json import dump
            dump(defaults, config_file_stream, indent=4)

        console.print('Configuration saved to ./app/harvest.json',
                      style='blue')
        from rich.text import Text
        console.print(Text('You may now start the Harvest API using the following command: ', style='green') +
                      Text('./launch\n', style='blue') +
                      Text(' or ', style='green') +
                      Text('./launch --with-mongo\n', style='blue'))


def ask(prompt: str, default: str = None, style: str = 'white', **kwargs) -> Any:
    from rich.prompt import Prompt
    from rich.text import Text

    result = Prompt.ask(prompt=Text('\n' + prompt, style=style),
                        default=None if default is None else str(default),
                        **kwargs)

    if default is None and result is None:
        result = None

    elif default is not None and result is None:
        result = default

    elif default is None and result is not None:
        result = result

    else:
        result = type(default)(result)

    return result


if __name__ == '__main__':
    from rich_argparse import RichHelpFormatter
    from argparse import ArgumentParser

    parser = ArgumentParser(description='Cloud Harvest API Configuration Tool',
                            formatter_class=RichHelpFormatter)
    parser.add_argument('--reset', action='store_true', help='Reset the configuration file to defaults')

    args = parser.parse_args()

    main(reset=args.reset)
