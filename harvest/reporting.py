
from base.tasks import BaseTaskChain
from logging import getLogger

logger = getLogger('harvest')


class Report(BaseTaskChain):
    def __init__(self, report_configuration: dict, match: tuple = (), add: tuple = (), limit: int = None, order: tuple = (), **kwargs):
        self.report_configuration = report_configuration
        self.add = add
        self.match = match
        self.limit = limit
        self.order = order

        super().__init__(name=report_configuration['name'])

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return None

    def build(self) -> dict:
        results = []


        return {
            "meta": {
                "StartTime": None,
                "EndTime": None,
                "Count": 0
            },
            "results": None,
        }


class ReportStatusCodes:
    pass
