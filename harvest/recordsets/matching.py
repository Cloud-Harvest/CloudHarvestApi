import operator
from collections import OrderedDict
from re import findall
from typing import List

# The order of _MATCH_OPERATIONS's keys is important. The keys should be ordered from longest to shortest to ensure that
# the longest match is attempted first. For example, '==' should be before '=' to ensure that '==' is matched
# before '='. This allows us to perform split() operations on the syntax without accidentally splitting on a substring
# that is part of the operator.
_MATCH_OPERATIONS = {
        '==': operator.eq,  # Checks if 'a' is equal to 'b'
        '>=': operator.ge,  # Checks if 'a' is greater than or equal to 'b'
        '<=': operator.le,  # Checks if 'a' is less than or equal to 'b'
        '!=': operator.ne,  # Checks if 'a' is not equal to 'b'
        '>': operator.gt,   # Checks if 'a' is greater than 'b'
        '<': operator.lt,   # Checks if 'a' is less than 'b'
        '=': findall        # Checks if 'a' contains 'b'
    }


class HarvestMatch:
    def __init__(self, syntax: str, record: OrderedDict = None):
        self._record = record or {}
        self._input = syntax
        self.key = None
        self.value = None

        self.operator = [op for op in _MATCH_OPERATIONS.keys() if op in syntax][0]
        self.final_match_operation = None
        self.is_match = None

    def as_mongo_match(self) -> dict:
        key = f'${self.key}'

        match self.operator:
            # https://www.mongodb.com/docs/manual/reference/operator/aggregation/regexMatch/
            case '=':
                result = {
                    "$regexMatch": {
                        "input": key,
                        "regex": self.value
                    }
                }

            case '<=':
                # https://www.mongodb.com/docs/manual/reference/operator/aggregation/lte/
                result = {
                    "$lte": {
                        [
                            key,
                            self.value
                        ]
                    }
                }

            case '>=':
                # https://www.mongodb.com/docs/manual/reference/operator/aggregation/gte/
                result = {
                    "$gte": {
                        [
                            key,
                            self.value
                        ]
                    }
                }
            case '==':
                # https://www.mongodb.com/docs/manual/reference/operator/aggregation/match/
                result = {
                    self.key: self.value
                }
            case '!=':
                # https://www.mongodb.com/docs/manual/reference/operator/aggregation/ne/
                # https://www.mongodb.com/docs/manual/reference/operator/aggregation/regexMatch/
                result = {
                    "$ne": [
                        {
                            "$regexMatch": {
                                "input": key,
                                "pattern": self.value
                            }
                        }
                    ]
                }

            case '<':
                # https://www.mongodb.com/docs/manual/reference/operator/aggregation/lt/
                result = {
                    "$lt": {
                        [
                            key,
                            self.value
                        ]
                    }
                }

            case '>':
                # https://www.mongodb.com/docs/manual/reference/operator/aggregation/gt/
                result = {
                    "$gt": {
                        [
                            key,
                            self.value
                        ]
                    }
                }

            case _:
                raise ValueError('No valid matching statement returned')

        return result

    def match(self) -> bool:
        self.key, self.value = self._input.split(self.operator, maxsplit=1)

        from .functions import is_bool, is_datetime, is_null, is_number
        matching_value = self.value
        record_key_value = self._record.get(self.key)

        # convert types if they do not match
        if type(matching_value) is not type(record_key_value):
            if is_bool(matching_value):
                cast_variables_as = 'bool'

            elif is_datetime(matching_value):
                cast_variables_as = 'datetime'

            elif is_null(matching_value):
                cast_variables_as = 'null'

            elif is_number(matching_value):
                cast_variables_as = 'float'

            else:
                cast_variables_as = 'str'

            from .functions import cast
            matching_value = cast(matching_value, cast_variables_as)
            record_key_value = cast(record_key_value, cast_variables_as)

        from re import findall, IGNORECASE
        if self.operator == '=':
            result = findall(pattern=matching_value, string=record_key_value, flags=IGNORECASE)

        else:
            result = _MATCH_OPERATIONS[self.operator](record_key_value, matching_value)

        self.final_match_operation = f'{record_key_value}{self.operator}{matching_value}'

        self.is_match = result

        return result


class HarvestMatchSet(list):
    def __init__(self, record: OrderedDict, syntax: str, matches: List[str]):
        super().__init__()

        self.original_syntax = syntax
        self._record = record

        self.matches = [HarvestMatch(record=record, syntax=match) for match in matches]
