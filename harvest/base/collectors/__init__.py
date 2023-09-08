from logging import getLogger
from base.exceptions import BaseDataCollectionException
from base.tasks import BaseTask, BaseTaskStatus

logger = getLogger('harvest')


class BaseDataCollectionTask(BaseTask):
    """
    BaseDataCollectionSteps contain the basic structure for running a form of data retrieval. The underlying collection
    logic is left to individual modules to define. This only provides the basic step-to-step framework.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # increment this any time Harvest performs an external operation
        self.api_calls = 0

        # one of BaseDataCollectionStatus
        self.status = BaseTaskStatus.initialized

    def run(self) -> list or BaseDataCollectionException:
        return self
