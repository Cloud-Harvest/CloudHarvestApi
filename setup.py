from setuptools import setup, find_packages

with open('requirements.txt') as f:
    required = f.read().splitlines()

config = dict(name='CloudHarvestApi',
              version='0.1.0',
              description='This is the API layer for CloudHarvest.',
              author='Cloud Harvest, Fiona June Leathers',
              url='https://github.com/Cloud-Harvest/CloudHarvestApi',
              packages=find_packages(include=['CloudHarvestApi']),
              install_requires=required,
              classifiers=[
                  'Programming Language :: Python :: 3.12',
              ],
              license='CC Attribution-NonCommercial-ShareAlike 4.0 International')


def main():
    setup(**config)


if __name__ == '__main__':
    main()
