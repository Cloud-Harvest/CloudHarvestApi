from typing import List
from .connection import HarvestCacheConnection

from tasks.base import BaseTask, TaskStatusCodes
from logging import getLogger

logger = getLogger('harvest')


class CacheAggregateTask(BaseTask):
    """
    A class used to represent a Cache Aggregate Task.

    This class is a subclass of the BaseTask class and is used to perform aggregation operations on a MongoDB collection.

    Attributes
    ----------
    collection : str
        The name of the MongoDB collection to perform the aggregation on.
    pipeline : List[dict]
        The aggregation pipeline to execute. This is a list of dictionaries, where each dictionary represents a stage in the pipeline.
    headers : dict, optional
        The headers to be used in the request.
    arguments : dict, optional
        Additional arguments to be used in the request.

    Methods
    -------
    run() -> 'BaseTask':
        Executes the CacheAggregateTask. This method will block until the task is completed.
    """

    def __init__(self, collection: str, pipeline: List[dict], arguments: dict = None, *args, **kwargs):
        """
        Constructs all the necessary attributes for the CacheAggregateTask object.

        Parameters
        ----------
            collection : str
                The name of the MongoDB collection to perform the aggregation on.
            pipeline : List[dict]
                The aggregation pipeline to execute. This is a list of dictionaries, where each dictionary represents a stage in the pipeline.
            arguments : dict, optional
                Additional arguments to be used in the request.
            *args:
                Variable length argument list.
            **kwargs:
                Arbitrary keyword arguments.
        """

        super().__init__(*args, **kwargs)

        self.collection = collection
        self.pipeline = pipeline
        self.headers = kwargs.get('headers')
        self.arguments = arguments or {}

    def run(self) -> 'BaseTask':
        """
        Executes the CacheAggregateTask. This method will block until the task is completed.

        Returns
        -------
        BaseTask
            The instance of the task.
        """

        connection = None

        try:
            self.status = TaskStatusCodes.running

            from cache.connection import HarvestCacheConnection
            from configuration import HarvestConfiguration

            connection = HarvestCacheConnection(**HarvestConfiguration.cache['connection'])
            result = aggregate(connection=connection,
                               collection=self.collection,
                               pipeline=self.pipeline,
                               **self.arguments)

            self.data = result.get('data')
            self.meta = result.get('meta', {}) | {'headers': self.headers}

        except Exception as ex:
            self.on_error(ex)

        else:
            self.on_complete()

        finally:
            if connection:
                connection.close()

        return self


def aggregate(connection: HarvestCacheConnection,
              collection: str,
              pipeline: List[dict],
              database: str = 'harvest',
              count: bool = False,
              ignore_user_filters: bool = False,
              add_keys: list = None,
              exclude_keys: list = None,
              matches: list = None,
              ) -> dict:

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

    if ignore_user_filters:
        pipeline_to_execute = pipeline

    else:
        pipeline_to_execute = apply_user_filters(pipeline=pipeline,
                                                 add_keys=add_keys,
                                                 exclude_keys=exclude_keys,
                                                 matches=matches)

    from templating.functions import template_object
    pipeline_to_execute = template_object(pipeline_to_execute)

    result = connection[database][collection].aggregate(pipeline=pipeline_to_execute, comment='harvest-api')

    if count:
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
        'pipeline': pipeline
    }

    return {
        'data': result,
        'meta': meta
    }


def apply_user_filters(pipeline: List[dict],
                       add_keys: list = None,
                       exclude_keys: list = None,
                       matches: list = None) -> List[dict]:
    """
    Applies user-defined filters to an aggregation pipeline.

    Parameters:
    pipeline (List[dict]): The aggregation pipeline to apply the filters to.
    add_keys (list, optional): A list of keys to add to the output. Defaults to None.
    exclude_keys (list, optional): A list of keys to exclude from the output. Defaults to None.
    matches (list, optional): A list of matching statements to apply to the pipeline. Defaults to None.

    Returns:
    List[dict]: The modified aggregation pipeline with the user-defined filters applied.

    Example:
    >>> apply_user_filters(pipeline, add_keys=['field1', 'field2'], exclude_keys=['field3'], header_order=['field2', 'field1'], matches=['field1=value'])
    [{'$addFields': {'field1': '$field1', 'field2': '$field2'}}, {'$project': {'field3': 0}}, {'$project': {'field2': 1, 'field1': 1}}, {'$match': {'field1': 'value'}}]
    """

    if matches:
        try:
            # This is a required plugin
            from recordsets.matching import HarvestMatch

            match_pipeline = []
            for match in matches:
                match = HarvestMatch(syntax=match)
                match_pipeline.append(match.as_mongo_match())

            pipeline.append({
                '$match': {
                    '$or': match_pipeline
                }
            })
        except ModuleNotFoundError:
            logger.warning('The core_data_model package is not installed. Cannot apply matching statements to the pipeline.')

    if add_keys:
        pipeline.append(
            {
                '$addFields': {
                    key: 1
                    for key in add_keys
                    if key not in (exclude_keys or [])
                }
            })

    return pipeline
