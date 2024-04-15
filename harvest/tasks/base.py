from .exceptions import BaseTaskException
from enum import Enum
from typing import List
from logging import getLogger


logger = getLogger('harvest')


class BaseTask:

    def __init__(self, name: str, **kwargs):
        self.name = name
        self.status = TaskStatusCodes.initialized

        self.previous_task = None
        self.data = None

    def run(self, *args, **kwargs):
        """
        Override this method with code to run a task.
        """
        pass

    def terminate(self):
        self.status = TaskStatusCodes.terminating


class TaskStatusCodes(Enum):
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

        # TODO: Check that any AsyncTask have a WaitTask at some point after it.

        self.name = name
        self._vars = {}

        self.position = 0

        self.status = TaskStatusCodes.initialized
        self.start = None
        self.end = None

        # from plugins.registry import PluginRegistry.
        # self.extend(initialize_objects(list_dict=tasks))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return None

    def run(self):
        from datetime import datetime, timezone
        self.status = TaskStatusCodes.running

        self.start = datetime.now(tz=timezone.utc)

        try:
            for i in range(len(self)):
                self.position = i

                if self.status == TaskStatusCodes.terminating:
                    break

                if i > 0:
                    self[i].previous_task = self[i - 1]

        except Exception as ex:
            raise BaseTaskException(*ex.args)

        finally:
            self.end = datetime.now(tz=timezone.utc)

            return self

    @property
    def detailed_progress(self) -> dict:
        """
        This method calculates and returns the progress of the task chain.

        It returns a dictionary with the following keys:
        - 'total': The total number of tasks in the task chain.
        - 'current': The current position of the task chain.
        - 'percent': The percentage of tasks completed in the task chain.
        - 'duration': The total duration of the task chain in seconds. If the task chain has not started, it returns 0.
        - 'counts': A dictionary with the count of tasks in each status. The keys of this dictionary are the status codes defined in the TaskStatusCodes Enum.

        Returns:
            dict: A dictionary representing the progress of the task chain.
        """

        from datetime import datetime, timezone
        count_result = {
            k: 0 for k in TaskStatusCodes
        }

        # iterate over tasks to get their individual status codes
        for task in self:
            count_result[task.status] += 1

        return {
            'total': len(self),
            'current': self.position,
            'percent': (self.position / len(self)) * 100,
            'duration': (self.end or datetime.now(tz=timezone.utc) - self.start).total_seconds() if self.start else 0,
            'counts': count_result
        }

    @property
    def percent(self) -> float:
        """
        Returns the current progress of the task chain as a percentage cast as float.
        """
        return self.position / self.total if self.total > 0 else -1

    @property
    def total(self) -> int:
        """
        Returns the total number of tasks in the task chain.
        """
        return len(self)

    def terminate(self):
        self.status = TaskStatusCodes.terminating
