
class Report:
    def __init__(self, report_configuration: dict, match: tuple = (), add: tuple = (), limit: int = None, order: tuple = (), **kwargs):
        self.report_configuration = report_configuration
        self.add = add
        self.match = match
        self.limit = limit
        self.order = order

        self.results = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return None

    def build(self) -> dict:
        from registry import Registry

        results = []

        for task_name, task_configuration in self.report_configuration.items():
            task_class = Registry.get_module(task_name)(**task_configuration)

        return {
            "meta": {
                "StartTime": None,
                "EndTime": None,
                "Count": 0
            },
            "results": None,
        }

class ReportStatusCodes:
