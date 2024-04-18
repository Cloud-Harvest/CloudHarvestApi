from tasks.base import BaseTask, TaskStatusCodes


class RecordSetTask(BaseTask):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def run(self, recordset_name: str, function: str, *args, **kwargs):

        recordset = self.task_chain.variables.get(recordset_name)

        try:
            self.status = TaskStatusCodes.running
            self.data = getattr(recordset, function)(*args, **kwargs)

        except Exception as ex:
            self.on_error(ex)

        else:
            self.on_complete()

        return self
