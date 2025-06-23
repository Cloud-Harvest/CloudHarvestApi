# CHANGELOG

## 0.3.7
- Updated to conform with CloudHarvestCoreTasks 0.8.0

## 0.3.6
- Code cleanup
- Will only update local cache if the results are not empty
- Added more logging outputs
- Improved redis request handling

## 0.3.5
- Updated to conform with CloudHarvestCoreTasks 0.7.0
- Updated the index definitions in the `harvest.yaml` file
- Flask HTTP log now routed to the main logger

## 0.3.4
- Added try when aggregating results in `tasks/get_task_status()` which prevented the status from being returned
- Fixed an issue with `tasks/list_tasks()` where the result was always an empty list


## 0.3.3
- Updated to conform with CloudHarvestCoreTasks 0.6.6

## 0.3.2
- Updated to conform with CloudHarvestCoreTasks 0.6.5

## 0.3.1
- Added `tasks/get_task_status`
- CloudHarvestCoreTasks 0.6.4
- [Part of the Redis Task Standardization Effort](https://github.com/Cloud-Harvest/CloudHarvestAgent/issues/8)
- Improved heartbeat by reducing the size of the upload payload
- Heartbeat will now send all datapoints per cycle to prevent scenarios where some fields are present and others are not
- Implemented 'pop' operation for `tasks/get_task_results`

## 0.3.0
- Refactor of the startup routine to be compatible with `gunicorn`
- Plugins are now handled by the CloudHarvestCorePluginManager

## 0.2.0
- Added endpoints
  - `pstar/list_platforms`
  - `pstar/list_services`
  - `pstar/list_pstar`
  - `pstar/queue_pstar`

## 0.1.15
- Updated to conform with CloudHarvestCoreTasks 0.6.3
- Added the `platforms` configuration option
- Added `pstar` endpoints
  - `list_accounts`
  - `list_platform_regions/<platform>` 

## 0.1.14
- Updated to conform with CloudHarvestCoreTasks 0.6.0
- Added error messages when failing to acquire silos
- Added `tasks/list_available_templates` endpoint
- Added `CachedData` class
  - Stores any data time in the `data` attribute
  - Stores when the data was recorded in the `recorded` attributes
  - Offers a `is_valid()` method which returns `True` if the data was recorded before the `age` property exceeds the `valid_age` property
- Added a `@use_cache_if_valid(cached_data: CachedData)` decorator which bypasses the method when the `CachedData.is_valid()` method returns `True`
- The Api no longer validates tasks from its own registry
  - Available tasks are now determined from `agent` node `available_templates` provided by the `agent` heartbeat
  - If the task does not exist, the Api will return a `NOT FOUND` error

## 0.1.13
- Updated to conform with CloudHarvestCoreTasks 0.4.1
- Updated to Python 3.13
- [`config.py`](./config.py)
  - Most prompts are now derived from [`config.yaml`](./config.yaml) 
- Implemented certificates in `harvest.yaml` with a default location of `harvest/certs`
- Added endpoint `tasks/list_available_tasks` to list all available tasks
- Added port number to the heartbeat record identifier

## 0.1.12
- Update to conform to CloudHarvestCoreTasks 0.4.0
- Added the `redis` service to `docker-compose.yaml`
- Moved several persistent cache operations to the ephemeral cache
- Moved `BaseCacheTask` and `CacheAggregateTask` to `CloudHarvestCoreTasks` as refactors inheriting `BaseDataTask`

## 0.1.11
- Updated `docker-compose` so that `mongo` manages its own data volume
- Fixed invalid `task_chain_from_dict()` arguments in `reports/routes.py`

## 0.1.10
- Updated to conform with CloudHarvestCoreTasks 0.3.0

## 0.1.9
- Updated to conform with CloudHarvestCorePluginManager 0.2.4

## 0.1.8
- Added log output for HarvestBlueprint
- Updated the report output to include the performance report
- Added custom JSONProvider which returns datetime objects in ISO format 

## 0.1.7
- Added `/` route and error codes.
- Removed some unused lines from `docker-compose.yaml`

## 0.1.6
- Changed the output of the [`report_run()`](CloudHarvestApi/blueprints/reports.py) method from `dict` to `List[dict]`
- Updated `BaseCacheTask` to accept the `title` parameter in the constructor

## 0.1.5
- Added `__register__.py` to capture definitions and instances.
- Added CloudHarvestCorePluginManager decorators to identify classes and instances to add to the Registry.
- `config.py` will now store plugins in `./app/api/plugins.txt`. 
  - This list will be used to install plugins. 
  - One installed, they can be activated using CloudHarvestCorePluginManager.registry.Registry.register_objects()
- Updated README

## 0.1.4
- Moved initiation to static class `CloudHarvestApi` to prevent re-instantiation when scanning for classes.
- Added CHANGELOG
