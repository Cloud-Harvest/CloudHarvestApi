from typing import List

from .base import BaseTask, BaseTaskChain, TaskStatusCodes


class AsyncTask(BaseTask):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class WaitTask(BaseTask):
    """
    The WaitTask class is a subclass of the BaseTask class. It represents a task that waits for certain conditions to be met before it can be run.

    Attributes:
        chain (BaseTaskChain): The task chain that this task belongs to.
        position (int): The position of this task in the task chain.
        check_time_seconds (float): The time interval in seconds at which this task checks if its conditions are met.
        _when_all_previous_async_tasks_complete (bool): A flag indicating whether this task should wait for all previous async tasks to complete.
        _when_all_previous_tasks_complete (bool): A flag indicating whether this task should wait for all previous tasks to complete.
        _when_all_tasks_by_name_complete (List[str]): A list of task names. This task will wait until all tasks with these names are complete.
        _when_any_tasks_by_name_complete (List[str]): A list of task names. This task will wait until any task with these names is complete.
    """

    def __init__(self,
                 chain: BaseTaskChain,
                 position: int,
                 check_time_seconds: float = 1,
                 when_all_previous_async_tasks_complete: bool = False,
                 when_all_previous_tasks_complete: bool = False,
                 when_all_tasks_by_name_complete: List[str] = None,
                 when_any_tasks_by_name_complete: List[str] = None,
                 **kwargs):

        """
        Initializes a new instance of the WaitTask class.

        Args:
            chain (BaseTaskChain): The task chain that this task belongs to.
            position (int): The position of this task in the task chain.
            check_time_seconds (float, optional): The time interval in seconds at which this task checks if its conditions are met. Defaults to 1.
            when_all_previous_async_tasks_complete (bool, optional): A flag indicating whether this task should wait for all previous async tasks to complete. Defaults to False.
            when_all_previous_tasks_complete (bool, optional): A flag indicating whether this task should wait for all previous tasks to complete. Defaults to False.
            when_all_tasks_by_name_complete (List[str], optional): A list of task names. This task will wait until all tasks with these names are complete. Defaults to None.
            when_any_tasks_by_name_complete (List[str], optional): A list of task names. This task will wait until any task with these names is complete. Defaults to None.
        """

        self.chain = chain
        self.position = position
        self.check_time_seconds = check_time_seconds
        self._when_all_previous_async_tasks_complete = when_all_previous_async_tasks_complete
        self._when_all_previous_tasks_complete = when_all_previous_tasks_complete
        self._when_all_tasks_by_name_complete = when_all_tasks_by_name_complete
        self._when_any_tasks_by_name_complete = when_any_tasks_by_name_complete

        super().__init__(**kwargs)

    def run(self):
        """
        Runs the task. This method will block until all conditions specified in the constructor are met.
        """

        from time import sleep

        while True:
            if any([
                self.when_all_previous_async_tasks_complete,
                self.when_all_previous_tasks_complete,
                self.when_all_tasks_by_name_complete,
                self.when_any_tasks_by_name_complete,
                self.status == TaskStatusCodes.terminating
            ]):
                break

            sleep(self.check_time_seconds)

    @property
    def when_all_previous_async_tasks_complete(self) -> bool:
        """
        Checks if all previous async tasks are complete.

        Returns:
            bool: True if all previous AsyncTasks are complete, False otherwise.
        """

        if self._when_all_previous_async_tasks_complete:
            return all([
                task.status in [
                    TaskStatusCodes.complete, TaskStatusCodes.error
                ]
                for task in self.chain[0:self.position]
                if isinstance(task, AsyncTask)
            ])

    @property
    def when_all_previous_tasks_complete(self) -> bool:
        """
        Checks if all previous tasks are complete.

        Returns:
            bool: True if all previous tasks are complete, False otherwise.
        """

        if self._when_all_previous_tasks_complete:
            return all([
                task.status in [
                    TaskStatusCodes.complete, TaskStatusCodes.error
                ]
                for task in self.chain[0:self.position]
            ])

    @property
    def when_all_tasks_by_name_complete(self) -> bool:
        """
        Checks if all tasks with the specified names are complete.

        Returns:
            bool: True if all tasks with the specified names are complete, False otherwise.
        """

        if self._when_all_tasks_by_name_complete:
            return all([
                task.status in [
                    TaskStatusCodes.complete, TaskStatusCodes.error
                ]
                for task in self.chain[0:self.position]
                if task.name in self._when_all_tasks_by_name_complete
            ])

    @property
    def when_any_tasks_by_name_complete(self) -> bool:
        """
        Checks if any task with the specified names is complete.

        Returns:
            bool: True if any task with the specified names is complete, False otherwise.
        """

        if self._when_any_tasks_by_name_complete:
            return any([
                task.status in [
                    TaskStatusCodes.complete, TaskStatusCodes.error
                ]
                for task in self.chain[0:self.position]
                if task.name in self._when_all_tasks_by_name_complete
            ])
