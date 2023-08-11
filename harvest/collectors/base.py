from logging import getLogger

logger = getLogger('harvest')


class BaseDataCollectionException(BaseException):
    def __init__(self, **kwargs):

        super(**kwargs).__init__()


class BaseDataCollectionStatus:
    """
    These are the basic status codes for any given data collection object.
    """
    complete = 'complete'           # the thread has stopped and there are no more tasks to complete
    error = 'error'                 # the thread has stopped in an error state
    initialized = 'initialized'     # the thread has been created
    running = 'running'             # the thread is currently processing data
    terminating = 'terminating'     # the thread was ordered to stop and is currently attempting to shut down


class DataCollectionModules:
    """
    A static class containing all data collection modules loaded into Harvest
    """
    modules = {}

    @staticmethod
    def add(collection_module_name: str, class_object: object):
        from importlib import import_module

        logger.debug(f'add data collection module {collection_module_name}')

        DataCollectionModules.modules[collection_module_name] = class_object

    @staticmethod
    def remove(collection_module_name: str):
        if DataCollectionModules.modules.get(collection_module_name):
            DataCollectionModules.modules.pop(collection_module_name)


class BaseDataCollectionStep:
    """
    BaseDataCollectionSteps contain the basic structure for running a form of data retrieval. The underlying collection
    logic is left to individual modules to define. This only provides the basic step-to-step framework.
    """
    def __init__(self, name: str, **kwargs):
        self.api_calls = 0                  # increment this any time Harvest performs an external operation
        self.initial_data = None            # added when moving between steps (usually the previous step's data)
        self.name = name                    # a descriptive name for this step
        self.result = None                  # {}, [{}], DataCollectionException

        # one of BaseDataCollectionStatus
        self.status = BaseDataCollectionStatus.initialized

    def run(self) -> list or BaseDataCollectionException:

        return self.result


class BaseDataCollector:
    def __init__(self, steps: list, **kwargs):
        self.steps = []

    def run(self):
        last_step_result = None

        for step in self.steps:
            step.initial_data = last_step_result

            last_step_result = step.run()


def get_collection_tasks(data_collection_tasks: list) -> tuple:
    for task in data_collection_tasks:
        yield DataCollectionModules.modules.get(task['step'])(**task)
