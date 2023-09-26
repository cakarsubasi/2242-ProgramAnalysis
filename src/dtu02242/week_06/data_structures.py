from dataclasses import dataclass
from typing import Any, Dict, List, Optional

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

def must_be_value(value_maybe: Any):
    if not value_maybe.__class__ is Value:
        raise Exception(f"{value_maybe} must be value!")

class Value:
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

    def __div__(self, other: 'Value'):
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
        must_be_value(__value)
        self._value.__setitem__(__idx, __value)

    def get_length(self):
        return self._capacity