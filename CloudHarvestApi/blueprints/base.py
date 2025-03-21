from flask import Request, Response, jsonify
from typing import Any


class CachedData:
    def __init__(self, data: Any, valid_age: float = 300.0):
        """
        A simple object which retains data and a timestamp of when it was recorded.

        Arguments
        data (Any): The data to store.
        valid_age (float): The age in seconds before the data is considered invalid. Default is 300 seconds (5 minutes).
        """

        from datetime import datetime
        self._data = data
        self._valid_age = valid_age
        self.recorded = datetime.now()

    @property
    def age(self) -> float:
        """
        Returns the age of the CachedData in seconds.
        """

        from datetime import datetime
        return (datetime.now() - self.recorded).total_seconds()

    @property
    def data(self) -> Any:
        """
        Returns the data stored in CachedData.
        """

        return self._data

    @property
    def is_valid(self) -> bool:
        """
        Returns whether the CachedData is still valid.
        """

        return self.age < self._valid_age

    @property
    def valid_age(self) -> float:
        """
        Returns the valid age of the CachedData in seconds.
        """

        return self._valid_age

    def update(self, data: Any, valid_age: float = None) -> 'CachedData':
        """
        Updates the data stored in CachedData.

        Arguments
        data (Any): The new data to store.
        valid_age (float): The age in seconds before the data is considered invalid. Default is valid_age assigned at initialization.

        Returns
        The CachedData object.
        """

        from datetime import datetime
        self._data = data
        self._valid_age = valid_age or self._valid_age
        self.recorded = datetime.now()

        return self

def safe_request_get_json(request: Request) -> dict:
    """
    Safely retrieves the JSON data from a request.
    :param request: The request to retrieve the JSON data from.
    :return: The JSON data from the request.
    """
    try:
        return request.get_json()

    except Exception as e:
        return {}


def safe_jsonify(success: bool, reason: str, result: Any, default: Any = None) -> Response:
    try:
        try_result = jsonify({
            'success': success,
            'reason': reason,
            'result': result
        })

    except Exception as ex:
        try_result = jsonify({
            'success': False,
            'reason': 'Failed to jsonify the result: ' + str(ex),
            'result': default
        })

    return try_result


def use_cache_if_valid(cached_data: CachedData):
    """
    A decorator to use cached data if it is still valid.
    :param cached_data: The CachedData object to use.
    :return: The cached data if it is still valid.
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            if cached_data.is_valid:
                return safe_jsonify(
                    success=True,
                    reason='OK',
                    result=cached_data.data
                )

            else:
                return func(*args, **kwargs)

        return wrapper

    return decorator
