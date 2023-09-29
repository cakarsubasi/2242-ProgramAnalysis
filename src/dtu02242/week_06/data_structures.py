from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

def wrap(arr: List[Any]) -> List['Value']:
    """
    Wrap a Python item in a Value
    """
    output = []
    for elem in arr:
        if type(elem) is list:
            output.append(ArrayValue(len(elem), [Value(each) for each in elem]))
        else:
            output.append(Value(elem))
    return output

def _must_be_value(value_maybe: Any):
    if not value_maybe.__class__ is Value:
        raise Exception(f"{value_maybe} must be value!")

class Value:
    value: Any
    type_name: str
    def __init__(self, value: Any, type_name: str = "void"):
        if type(value) is Value:
            raise Exception("Values shouldn't be nested!")
        self._value = value
        if type_name is None:
            self.type_name = type(value).__name__
        else:
            self.type_name = type_name

    def _type_check(self, other: 'Value') -> Optional[str]:
        return self.type_name

    def __add__(self, other: 'Value'):
        return Value(self._value + other._value, self.type_name)

    def __sub__(self, other: 'Value'):
        return Value(self._value - other._value, self.type_name)

    def __mul__(self, other: 'Value'):
        return Value(self._value * other._value, self.type_name)

    def __truediv__(self, other: 'Value'):
        return Value(self._value / other._value, self.type_name)

    def __eq__(self, other: 'Value'):
        return self._value == other._value

    def __le__(self, other: 'Value'):
        return self._value <= other._value

    def __gt__(self, other:'Value'):
        return self._value > other._value

    def __str__(self):
        return str(self._value)

    def __repr__(self):
        return f"{self.type_name}:{repr(self._value)}"
    
    def get_value(self) -> Any:
        return self._value

    
class ValueRange(Value):
    def __init__(self, value: Any, type_name: str = "void"):
        super().__init__(value, type_name)


class JavaError:
    # Need a way of propagating errors
    # Probably best to discuss how to implement this before deciding on one
    pass


class OutputBuffer:
    buffer: str = ""
    def push(self, str_or_bytes):
        self.buffer += str_or_bytes


@dataclass
class RefValue:
    # refvalue should contain a pointer
    # to another structure
    value: Any


@dataclass
class ClassValue:
    class_name: str
    fields: Dict[str, RefValue]


class ArrayValue(Value):
    _value: List[Value]
    _capacity: int

    def __init__(self, capacity: int, fill: Value | List[Value], type_name: str = "list:void"):
        self._capacity = capacity
        if type(fill) is Value:
            self._value = [fill for _ in range(capacity)]
        elif type(fill) is list:
            self._value = fill
            assert capacity == len(fill)
            for elem in self._value:
                assert type(elem) is Value

    def __getitem__(self, __idx) -> Value:
        return self._value.__getitem__(__idx)
    
    def __setitem__(self, __idx, __value: Value):
        _must_be_value(__value)
        self._value.__setitem__(__idx, __value)

    def get_length(self):
        return self._capacity


# TODO: Write Abstractions here

class Range:
    pass
    # Gotta figure out a good range abstraction

@dataclass
class NeverReturn:
    pass
    # We need a way to indicate that a function is divergent
    # (ie never returns)
    def __eq__(self, __value: object) -> bool:
        return type(self) is type(__value)

@dataclass
class MaybeReturn:
    pass
    def __eq__(self, __value: object) -> bool:
        return type(self) is type(__value)

class Assumption:
    # An assumption should be a constraint, indicating either
    # working constraints (assertions or otherwise) or
    # conditions required for a certain event to happen
    def __init__(self) -> None:
        raise NotImplementedError()

    def __eq__(self, __value: object) -> bool:
        raise NotImplementedError()

@dataclass   
class AnalysisError:
    name: str
    constraint: Assumption
    cause: Optional[str]

    def __eq__(self, __value: 'AnalysisError') -> bool:
        if type(__value) is not AnalysisError:
            return False
        return self.name == __value.name
    
    def __hash__(self) -> int:
        # this treats every type of error as one instance
        # which is generally not what you want
        return self.name.__hash__()

# Errors should be in the format:
# error_name, constraint(s?), cause (maybe drop this for now)

class AnalysisResult(Value):
    errors: List[AnalysisError]
    # Asserts always give the same error so, we only carry the assumption
    asserts: List[Assumption]
    def __init__(self, return_value: Any , type_name: str = "analysis_result"):
        super().__init__(return_value, type_name)
        errors = []
        asserts = []
        # TODO

    def __eq__(self, other: 'Value'):
        if type(other) is Value:
            return super().__eq__(other) and len(self.errors) == 0
        elif type(other) is AnalysisResult:
            same_return = self.value == other.value
            # this treats every type of one error as unique
            # we may probably wish to change this later on
            same_errors = set(self.errors) == set(other.errors)
            # might also want to compare assumptions
            return same_return and same_errors
            
        else:
            return False 
        
    

