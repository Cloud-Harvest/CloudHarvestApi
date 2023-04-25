from datetime import datetime


def duration_in_seconds(a: datetime, b: datetime) -> int or float:
    """
    a simple, testable function for retrieving the number of seconds between two dates
    :param a: a datetime
    :param b: another datetime
    :return: an integer or float representing the number of seconds between two datetime objects
    """

    return abs((a - b).total_seconds())
