from setuptools import setup, find_packages
from CloudHarvestApi.meta import meta

with open('requirements.txt') as f:
    required = f.read().splitlines()

config = dict(packages=find_packages(include=['CloudHarvestApi']),
              install_requires=required)

config = config | meta


def main():
    setup(**config)


if __name__ == '__main__':
    main()
