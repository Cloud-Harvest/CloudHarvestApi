from typing import List
from .connection import HarvestCacheConnection

from tasks.base import BaseTask, TaskStatusCodes
from logging import getLogger

logger = getLogger('harvest')


class BaseCacheTask(BaseTask):
    def __init__(self, pipeline: List[dict],
                 collection: str,
                 database: str = 'harvest',
                 ignore_user_filters: bool = False,
                 add_keys: List[str] = None,
                 count: bool = False,
                 exclude_keys: List[str] = None,
                 headers: List[str] = None,
                 limit: int = None,
                 matches: List[List[str]] = None,
                 *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.ignore_user_filters = ignore_user_filters

        self.connection = None

        self.database = database
        self.collection = collection
        self.pipeline = pipeline
        self.add_keys = add_keys or []
        self.count = count
        self.headers = headers or []
        self.exclude_keys = exclude_keys or []
        self.limit = limit
        self.matches = matches or []

        if self.ignore_user_filters:
            pipeline_to_execute = self.pipeline

        else:
            pipeline_to_execute = self.prepare_pipeline()

        from templating.functions import template_object
        self.pipeline_to_execute = template_object(pipeline_to_execute)

    def prepare_pipeline(self) -> List[dict]:
        """
        Applies user-defined filters to an aggregation pipeline.

        Returns:
        List[dict]: The modified aggregation pipeline with the user-defined filters applied.
        """

        if self.ignore_user_filters:
            return self.pipeline

        pipeline = self.pipeline.copy()

        if self.matches:
            # This is a required plugin
            from recordsets.matching import HarvestMatchSet

            match_pipeline = []
            for matches in self.matches:
                match_set = HarvestMatchSet(matches=matches)
                match_pipeline.append(match_set.as_mongo_match())

            if len(match_pipeline) == 0:
                pass

            elif len(match_pipeline) == 1:
                pipeline.append({
                    '$match': match_pipeline[0]
                })

            else:
                pipeline.append({
                    '$match': {
                        '$or': match_pipeline
                    }
                })

        if self.add_keys:
            self.pipeline.append(
                {
                    '$addFields': {
                        key: 1
                        for key in self.add_keys
                        if key not in (self.exclude_keys or [])
                    }
                })

        if self.limit:
            pipeline.append({
                '$limit': self.limit
            })

        return pipeline

    def aggregate(self) -> dict:

        """
        Executes a MongoDB aggregation pipeline on a specified database and collection in the Harvest cache.

        Parameters:
        connection (HarvestCacheConnection): The connection to the MongoDB instance.
        collection (str): The name of the collection to perform the aggregation on.
        pipeline (List[dict]): The aggregation pipeline to execute. This is a list of dictionaries, where each dictionary represents a stage in the pipeline.
        database (str, optional): The name of the database where the collection resides. Defaults to 'harvest'.
        count (bool, optional): If set to True, the function will return the count of documents that match the pipeline. If False, it will return the actual documents. Defaults to False.
        ignore_user_filters (bool, optional): If set to True, the function will ignore any user-defined filters. Defaults to False.
        add_keys (list, optional): A list of keys to add to the output. Defaults to None.
        exclude_keys (list, optional): A list of keys to exclude from the output. Defaults to None.
        matches (list, optional): A list of matching statements to apply to the pipeline. Defaults to None.

        Returns:
        dict: The result of the aggregation. If count is True, this will be an integer representing the count of matching documents. If False, this will be a list of the matching documents. The return value also includes metadata about the execution of the pipeline, such as start time, end time, duration, and the pipeline itself.

        Example:
        >>> aggregate(connection, 'myCollection', [{'$match': {'field': 'value'}}], ignore_user_filters=True, add_keys=['field1', 'field2'], exclude_keys=['field3'], matches=['field1=value'])
        {'data': [...], 'meta': {...}}
        """

        from datetime import datetime, timezone
        start = datetime.now(tz=timezone.utc)

        result = self.connection[self.database][self.collection].aggregate(pipeline=self.pipeline_to_execute,
                                                                           comment='harvest-api')

        if self.count:
            result = len(list(result))

        else:
            result = [
                {
                    k: str(v) if k == '_id' else v
                    for k, v in doc.items()
                }
                for doc in result
            ]

        end = datetime.now(tz=timezone.utc)

        meta = {
            'start': start,
            'end': end,
            'duration': (end - start).total_seconds(),
            'pipeline': self.pipeline
        }

        return {
            'data': result,
            'meta': meta
        }

    def get_headers(self) -> list:
        """
        This method is used to get the headers for the task. It combines the headers and add_keys attributes,
        excluding any keys that are in the exclude_keys attribute.

        Returns:
            list: A list of headers for the task. The list includes the headers and add_keys attributes,
            excluding any keys that are in the exclude_keys attribute.

        Example:
            Assuming the headers attribute is ['header1', 'header2'], add_keys is ['header3', 'header4'],
            and exclude_keys is ['header2'], calling this method would return ['header1', 'header3', 'header4'].
        """

        result = []
        if self.headers:
            result = [
                h for h in self.headers + [a for a in self.add_keys if a not in self.headers]
                if h not in self.exclude_keys
            ]

        return result


class CacheAggregateTask(BaseCacheTask):
    """
    A class used to represent a Cache Aggregate Task.

    This class is a subclass of the BaseCacheTask class and is used to perform aggregation operations on a MongoDB collection.

    Methods
    -------
    run() -> 'BaseTask':
        Executes the CacheAggregateTask. This method will block until the task is completed.
    """

    def __init__(self, *args, **kwargs):
        """
        Constructs all the necessary attributes for the CacheAggregateTask object.

        Parameters
        ----------
            *args:
                Variable length argument list.
            **kwargs:
                Arbitrary keyword arguments.
        """

        super().__init__(*args, **kwargs)

    def run(self) -> 'BaseTask':
        """
        Executes the CacheAggregateTask. This method will block until the task is completed.

        Returns
        -------
        BaseTask
            The instance of the task.
        """

        try:
            self.status = TaskStatusCodes.running

            from cache.connection import HarvestCacheConnection
            from configuration import HarvestConfiguration
            self.connection = HarvestCacheConnection(**HarvestConfiguration.cache['connection'])

            result = self.aggregate()

            self.data = result.get('data')
            self.meta = result.get('meta', {}) | {'headers': self.get_headers()}

        except Exception as ex:
            self.on_error(ex)

        else:
            self.on_complete()

        finally:
            if self.connection:
                self.connection.close()

        return self
