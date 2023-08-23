"""
modules.py - module loading logic
"""
from logging import getLogger
from subprocess import run

logger = getLogger('harvest')


class ModuleRegister:
    loaded_modules = []


def clone_repositories(repos: list, path: str) -> dict:
    # check if git is installed
    if run(args=['git', '--version']).returncode != 0:
        raise FileNotFoundError('git was not found in the path',
                                'git is required to retrieve remote modules')

    # create module_path if it exists
    from pathlib import Path
    p = Path(path).expanduser()
    p.mkdir(parents=True, exist_ok=True)

    # clone repositories
    results = {}
    for repo in repos:
        module_name = [str(s).replace('.git', '')
                       for s in repo["source"].split('/')
                       if '.git' in s][0]

        logger.debug(f'clone: {repo["source"]}')

        args = ['git',
                'clone',
                '--recurse-submodules',
                '--single-branch']

        if repo.get('label'):
            args.append(f'--branch={repo["label"]}')

        from os.path import join
        module_destination = join(path, module_name)

        r = run(args=args + [repo["source"], module_destination])

        if r.returncode == 0:
            logger.debug(f'clone: OK: {repo["source"]} -> {module_destination}')

        else:
            logger.error(f'clone: error when attempting to retrieve {repo["source"]}')

        results[module_name] = {
            **repo,
            "status": r.returncode
        }

    return results
