# 0.1.11
- Updated `docker-compose` so that `mongo` manages its own data volume
- Fixed invalid `task_chain_from_dict()` arguments in `reports/routes.py`

# 0.1.10
- Updated to conform with CloudHarvestCoreTasks 0.3.0

# 0.1.9
- Updated to conform with CloudHarvestCorePluginManager 0.2.4

# 0.1.8
- Added log output for HarvestBlueprint
- Updated the report output to include the performance report
- Added custom JSONProvider which returns datetime objects in ISO format 

# 0.1.7
- Added `/` route and error codes.
- Removed some unused lines from `docker-compose.yaml`

# 0.1.6
- Changed the output of the [`report_run()`](CloudHarvestApi/api/blueprints/reports/routes.py) method from `dict` to `List[dict]`
- Updated `BaseCacheTask` to accept the `title` parameter in the constructor

# 0.1.5
- Added `__register__.py` to capture definitions and instances.
- Added CloudHarvestCorePluginManager decorators to identify classes and instances to add to the Registry.
- `config.py` will now store plugins in `./app/plugins.txt`. 
  - This list will be used to install plugins. 
  - One installed, they can be activated using CloudHarvestCorePluginManager.registry.Registry.register_objects()
- Updated README

# 0.1.4
- Moved initiation to static class `CloudHarvestApi` to prevent re-instantiation when scanning for classes.
- Added CHANGELOG
