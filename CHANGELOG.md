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
