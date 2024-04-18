from .base import BaseTaskChain, TaskStatusCodes


# class Report(BaseTaskChain):
#     def __init__(self, name: str, task_templates: list, *args, **kwargs):
#         super().__init__(name=name, task_templates=task_templates, *args, **kwargs)
#
#     def run(self, *args, **kwargs):
#         self.status = TaskStatusCodes.running
#         self.on_complete()
#         return self
