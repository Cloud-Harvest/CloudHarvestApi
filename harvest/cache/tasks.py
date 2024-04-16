from typing import Any, List
from .connection import HarvestCacheConnection

from tasks.base import BaseTask, TaskStatusCodes
from logging import getLogger

logger = getLogger('harvest')


class CacheTask(BaseTask):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def run(self, *args, **kwargs) -> 'BaseTask':
        try:
            self.status = TaskStatusCodes.running

            from cache.connection import HarvestCacheConnection
            from configuration import HarvestConfiguration

            connection = HarvestCacheConnection(**HarvestConfiguration.cache['connection'])
            self.data = aggregate(connection=connection,
                                  **kwargs)

        except Exception as ex:
            self.on_error(ex)

        else:
            self.on_complete()

        return self


def aggregate(connection: HarvestCacheConnection,
              collection: str,
              pipeline: List[dict],
              database: str = 'harvest',
              count: bool = False) -> Any:

    """
    Executes a MongoDB aggregation pipeline on a specified database and collection in the Harvest cache.

    Parameters:
    connection (HarvestCacheConnection): The connection to the MongoDB instance.
    collection (str): The name of the collection to perform the aggregation on.
    pipeline (List[dict]): The aggregation pipeline to execute. This is a list of dictionaries, where each dictionary represents a stage in the pipeline.
    database (str, optional): The name of the database where the collection resides. Defaults to 'harvest'.
    count (bool, optional): If set to True, the function will return the count of documents that match the pipeline. If False, it will return the actual documents. Defaults to False.

    Returns:
    Any: The result of the aggregation. If count is True, this will be an integer representing the count of matching documents. If False, this will be a list of the matching documents. The return value also includes metadata about the execution of the pipeline, such as start time, end time, duration, and the pipeline itself.

    Example:
    >>> aggregate(connection, 'myCollection', [{'$match': {'field': 'value'}}])
    {'result': [...], 'meta': {...}}
    """

    from datetime import datetime, timezone
    start = datetime.now(tz=timezone.utc)

    result = [
        doc for doc in connection[database][collection].aggregate(pipeline=pipeline,
                                                                  comment='harvest-api')
    ]

    end = datetime.now(tz=timezone.utc)

    meta = {
        'start': start,
        'end': end,
        'duration': (end - start).total_seconds(),
        'pipeline': pipeline
    }

    return {
        'result': len(result) if count else result,
        'meta': meta
    }
