from base.exceptions import BaseTaskException
from typing import List
from logging import getLogger
from plugins import initialize_object


logger = getLogger('harvest')


class BaseTask:

    def __init__(self, name: str, **kwargs):
        self.name = name
        self.status = None

        self.previous_task = None
        self.data = None

    def __init_subclass__(cls, **kwargs):
        from plugins import PluginRegistry
        super().__init_subclass__(**kwargs)
        PluginRegistry.objects[cls.__name__] = cls


class BaseTaskStatus:
    """
    These are the basic status codes for any given data collection object.
    """
    complete = 'complete'           # the thread has stopped and there are no more tasks to complete
    error = 'error'                 # the thread has stopped in an error state
    initialized = 'initialized'     # the thread has been created
    running = 'running'             # the thread is currently processing data
    terminating = 'terminating'     # the thread was ordered to stop and is currently attempting to shut down


class BaseTaskChain(List[BaseTask]):
    def __init__(self, name: str, tasks: List[dict]):
        super().__init__()

        self.name = name
        self._vars = {}

        self.position = 0

        self.status = BaseTaskStatus.initialized

        from plugins import initialize_objects
        self.extend(initialize_objects(list_dict=tasks))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return None

    def run(self):
        self.status = BaseTaskStatus.running

        try:
            for i in range(len(self)):
                self.position = i

                if self.status == BaseTaskStatus.terminating:
                    break

                if i > 0:
                    self[i].previous_task = self[i - 1]

        except Exception as ex:
            raise BaseTaskException(*ex.args)

        finally:
            return self

    @property
    def total(self):
        return len(self)

    def terminate(self):
        self.status = BaseTaskStatus.terminating
