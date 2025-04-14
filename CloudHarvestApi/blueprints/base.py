from CloudHarvestCoreTasks.cache import CachedData

from flask import Request, Response, jsonify
from typing import Any


########################################################################################################################
# FUNCTIONS
########################################################################################################################
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


########################################################################################################################
# DECORATORS
########################################################################################################################
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
