from CloudHarvestCoreTasks.cache import CachedData
from CloudHarvestCoreTasks.silos import BaseSilo

from flask import Request, Response, jsonify
from logging import getLogger
from typing import Any

logger = getLogger('harvest')

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

class RedisRequest:
    def __init__(self, silo: str or BaseSilo, max_attempts: int = 10):

        self.silo = silo
        self.max_attempts = max_attempts

        self.client = None

    def __enter__(self):
        """
        Context manager to enter the RedisRequest.
        """
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Context manager to exit the RedisRequest.
        """
        # No specific cleanup needed for RedisRequest
        if self.client:
            try:
                self.client.close()
            except Exception as e:
                pass
        pass

    def __getattr__(self, name):
        """
        Dynamically wrap StrictRedis methods with retry logic.
        """

        def wrapper(*args, **kwargs):
            from CloudHarvestCoreTasks.silos import get_silo
            self.silo = get_silo(self.silo) if isinstance(self.silo, str) else self.silo

            for i in range(self.max_attempts):
                try:
                    self.client = self.silo.connect()

                    logger.debug(f'{self.silo.name}: {name}')

                    result = getattr(self.client, name)(*args, **kwargs)
                    return result

                except BaseException as ex:
                    if i < self.max_attempts - 1:
                        logger.debug(f"Error querying Redis ({i + 1}/{self.max_attempts}): {ex}")
                        from time import sleep
                        sleep(1)
                        continue

                    else:
                        from traceback import format_exc
                        logger.error(f"Failed to query Redis after {self.max_attempts} attempts: {ex}\n{format_exc()}")
                        raise

        return wrapper


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
