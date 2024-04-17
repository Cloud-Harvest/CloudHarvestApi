from .exceptions import BaseTaskException
from enum import Enum
from typing import Any, List
from logging import getLogger


logger = getLogger('harvest')

# TODO: (Async)TemplateTask (a task that generates more tasks from a template) with parameters to insert the new tasks
#       into a specific task chain position (or immediately following itself)


class TaskStatusCodes(Enum):
    """
    These are the basic status codes for any given data collection object.
    """
    complete = 'complete'           # the thread has stopped and there are no more tasks to complete
    error = 'error'                 # the thread has stopped in an error state
    initialized = 'initialized'     # the thread has been created
    running = 'running'             # the thread is currently processing data
    terminating = 'terminating'     # the thread was ordered to stop and is currently attempting to shut down


class TaskRegistry:
    """
    This class is a registry for all tasks available in the program. Tasks are automatically added when they inherit
    BaseTask. As a result, all tasks should inherit BaseTask even if they do not use the BaseTask functionality.
    """
    tasks = {}

    @staticmethod
    def task_class_by_name(name: str) -> 'BaseTask' or None:
        return TaskRegistry.tasks.get(name)


class BaseTask:
    def __init__(self,
                 name: str,
                 description: str = None,
                 task_chain: 'BaseTaskChain' = None,
                 result_as: str = None,
                 **kwargs):

        self.name = name
        self.description = description
        self.task_chain = task_chain
        self.result_as = result_as
        self.status = TaskStatusCodes.initialized

        self.previous_task = None
        self.data = None
        self.meta = None

    def run(self, function: Any, *args, **kwargs) -> 'BaseTask':
        """
        Override this method with code to run a task.
        """
        try:
            self.status = TaskStatusCodes.running
            self.data = function(*args, **kwargs)

        except Exception as ex:
            self.on_error(ex)

        else:
            self.on_complete()

        return self

    def on_complete(self) -> 'BaseTask':
        """
        Override this method with code to run when a task completes.
        """
        if self.result_as and self.task_chain:
            self.task_chain.vars[self.result_as] = self.data

        self.status = TaskStatusCodes.complete

        return self

    def on_error(self, ex: Exception) -> 'BaseTask':
        """
        Override this method with code to run when a task errors.
        """
        self.status = TaskStatusCodes.error

        if hasattr(ex, 'args'):
            self.meta = ex.args

        logger.error(f'Error running task {self.name}: {ex}')

        return self

    def terminate(self) -> 'BaseTask':
        self.status = TaskStatusCodes.terminating
        logger.warning(f'Terminating task {self.name}')

        return self

    def __init_subclass__(cls, **kwargs):
        """
        This method is called when a subclass of BaseTask is created.
        """
        super().__init_subclass__(**kwargs)

        if cls.__name__ not in TaskRegistry.tasks:
            TaskRegistry.tasks[cls.__name__.lower()[0:-4]] = cls

    def __dict__(self) -> dict:
        return {
            'name': self.name,
            'description': self.description,
            'status': self.status,
            'data': self.data,
            'meta': self.meta
        }


class BaseAsyncTask(BaseTask):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.thread = None

    def run(self, *args, **kwargs) -> 'BaseAsyncTask':
        """
        Override this method with code to run a task asynchronously.
        """
        from threading import Thread

        self.thread = Thread(target=self._run, args=args, kwargs=kwargs)
        self.thread.start()

        self.status = TaskStatusCodes.running

        return self

    def _run(self, *args, **kwargs):
        """
        Override this method with code to run a task.
        """
        pass

    def terminate(self) -> 'BaseAsyncTask':
        super().terminate()
        self.thread.join()

        return self


class BaseTaskChain(List[BaseTask]):
    def __init__(self, name: str, tasks: List[dict]):
        super().__init__()

        # TODO: Check that any AsyncTask (except PruneTask) have a WaitTask at some point after it.

        self.name = name
        self.vars = {}
        self._initial_task_templates = tasks

        self.position = 0

        self.status = TaskStatusCodes.initialized
        self.start = None
        self.end = None

        # from plugins.registry import PluginRegistry.
        # self.extend(initialize_objects(list_dict=tasks))

    def __enter__(self) -> 'BaseTaskChain':
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return None

    def run(self) -> 'BaseTaskChain':
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

    def terminate(self) -> 'BaseTaskChain':
        self.status = TaskStatusCodes.terminating

        return self
