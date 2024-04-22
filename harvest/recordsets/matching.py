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
        '=>': operator.ge,  # Checks if 'a' is greater than or equal to 'b'
        '<=': operator.le,  # Checks if 'a' is less than or equal to 'b'
        '=<': operator.le,  # Checks if 'a' is less than or equal to 'b'
        '!=': operator.ne,  # Checks if 'a' is not equal to 'b'
        '>': operator.gt,   # Checks if 'a' is greater than 'b'
        '<': operator.lt,   # Checks if 'a' is less than 'b'
        '=': findall        # Checks if 'a' contains 'b'
    }


class HarvestMatch:
    def __init__(self, syntax: str, record: OrderedDict = None):
        self._record = record or {}
        self.syntax = syntax
        self.key = None
        self.value = None

        self.operator = self.get_operator_key()
        self.final_match_operation = None
        self.is_match = None

    def as_mongo_match(self) -> dict:
        if self.key is None and self.value is None:
            self.key, self.value = self.syntax.split(self.operator, maxsplit=1)

            # strip whitespace from the key, value, and operator
            for v in ['key', 'value', 'operator']:
                if hasattr(getattr(self, v), 'strip'):
                    setattr(self, v, getattr(self, v).strip())

            # fuzzy cast the value to the appropriate type
            from .functions import fuzzy_cast
            self.value = fuzzy_cast(self.value)

            if self.value is None:
                return {
                    self.key: None
                }

        key = f'${self.key}'

        match self.operator:
            # https://www.mongodb.com/docs/manual/reference/operator/aggregation/regexMatch/
            case '=':
                result = {
                    "$regexMatch": {
                        "input": {
                            "$toString": key
                        },
                        "regex": str(self.value),       # $regexMatch requires a string
                        "options": "i"
                    }
                }

            case '<=' | '=<':
                # https://www.mongodb.com/docs/manual/reference/operator/aggregation/lte/
                result = {
                    self.key: {
                        "$lte": self.value
                    }
                }

            case '>=' | '=>':
                # https://www.mongodb.com/docs/manual/reference/operator/aggregation/gte/
                result = {
                    self.key: {
                        "$gte": self.value
                    }
                }

            case '==':
                # https://www.mongodb.com/docs/manual/reference/operator/aggregation/match/
                result = {
                    self.key: self.value
                }

            case '!=':
                # https://www.mongodb.com/docs/manual/reference/operator/aggregation/not/
                # https://www.mongodb.com/docs/manual/reference/operator/aggregation/regexMatch/
                result = {
                    "$not": {
                        "$regexMatch": {
                            "input": {
                                "$toString": key
                            },
                            "regex": str(self.value),       # $regexMatch requires a string
                            "options": "i"
                        }
                    }
                }

            case '<':
                # https://www.mongodb.com/docs/manual/reference/operator/aggregation/lt/
                result = {
                    self.key: {
                        "$lt": self.value
                    }
                }

            case '>':
                # https://www.mongodb.com/docs/manual/reference/operator/aggregation/gt/
                result = {
                    self.key: {
                        "$gt": self.value
                    }
                }

            case _:
                raise ValueError('No valid matching statement returned')

        return result

    def match(self) -> bool:
        self.key, self.value = self.syntax.split(self.operator, maxsplit=1)

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

    def get_operator_key(self):
        for op in _MATCH_OPERATIONS.keys():
            if op in self.syntax:
                return op

        raise ValueError('No valid operator found in syntax. Valid operators are: ' + ', '.join(_MATCH_OPERATIONS.keys()))


class HarvestMatchSet(list):
    def __init__(self, matches: List[str], record: OrderedDict = None):
        super().__init__()

        self._record = record

        self.matches = [HarvestMatch(record=record, syntax=match) for match in matches]

    def as_mongo_match(self) -> dict:
        result = {}
        expr = {'$expr': {'$and': []}}
        non_expr = {}

        for match in self.matches:
            match_syntax = match.as_mongo_match()
            if list(match_syntax.keys())[0].startswith('$'):
                expr['$expr']['$and'].append(match_syntax)

            else:
                non_expr.update(match_syntax)

        if expr['$expr']['$and']:
            result.update(expr)

        if non_expr:
            result.update(non_expr)

        return result
