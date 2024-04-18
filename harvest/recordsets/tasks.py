from tasks.base import BaseTask, TaskStatusCodes
from .recordset import HarvestRecordSet


class RecordSetTask(BaseTask):
    def __init__(self, recordset_name: HarvestRecordSet, function: str, arguments: dict, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.recordset_name = recordset_name
        self.function = function
        self.arguments = arguments

    def run(self):

        recordset = self.task_chain.get_variables_by_names(self.recordset_name)

        try:
            self.status = TaskStatusCodes.running
            self.data = getattr(recordset, self.function)(**self.arguments)

        except Exception as ex:
            self.on_error(ex)

        else:
            self.on_complete()

        return self
