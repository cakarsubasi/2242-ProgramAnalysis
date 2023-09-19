from typing import Dict, List, Any
from dataclasses import dataclass
from .parser import JavaClass, JavaProgram

"""
noop
push empty
push value
store
load
    ref
    int
newarray
array_load
dup
binary
    addition
    subtraction
    multiplication
    division
    modulo
ifz
    le
    ne
if
    le
"""

@dataclass
class IntValue:
    # Note that python ints are bigints
    # and you may wish to use ctypes
    # for a more Java like int representation
    value: int

@dataclass
class ShortValue:
    value: int

@dataclass
class RefValue:
    type: str
    # refvalue should contain a pointer
    # to a mutable data structure
    # the simplest one in Python is the list
    value: List[Any]
    # Also keep in mind that to emulate Java
    # behavior, we need reference counting
    # semantics but right now it is likely
    # simpler to just leak all memory

    # Copies made of this dataclass should
    # copy the pointer allowing different
    # instances to refer to the same data

    def __init__(self, type: str, value: Any):
        self.type = type
        self.value = [value]

    def __getattr__(self, name: str):
        # unwrap the value to not pass a list
        if name == "value":
            return self.value[0]
        else:
            return getattr(self, name)

@dataclass
class BoolValue:
    value: bool

@dataclass
class ByteValue:
    # TODO: use a better byte
    value: int



JavaValue = IntValue | BoolValue | ByteValue | ShortValue | RefValue

class Value:

    def __init__(self, type_name: str, value: JavaValue):
        self.type_name = type_name
        self.value = value

class Counter:

    def __init__(self, method_name: str, counter: int):
        self.method_name = method_name
        self.counter = counter

class StackElement:

    def __init__(self, counter: Counter):
        self.local_variables: List[Value] = []
        self.operational_stack: List[Value] = []
        self.counter: Counter = counter

class Interpreter:

    def __init__(self, json_program):
        self.memory: Dict[str, Value] = {}
        self.stack: List[StackElement] = json_program
        self.json_program = json_program

    def run(self):
        if len(self.stack) == 0:
            return
        element = self.stack.pop(-1)
        # operation = self.json_program.bytecode[element.method_name][element.counter]
        operation = element
        self.run_operation(operation)
        self.run()

    def run_operation(self, operation):
        method = method_mapper[operation]
        method(self)


def perform_noop(runner: Interpreter):
    print("example")

def perform_add(runner: Interpreter):
    runner.stack.append("noop")
    print("add")

method_mapper = {
    "noop": perform_noop,
    "add": perform_add,
}

#runner = Interpreter(["add", "add"])
#runner.run()

def run_program():
    raise NotImplementedError

def run_method(java_class: JavaClass, method_name: str, method_args: Dict[str, JavaValue]) -> JavaValue:
    raise NotImplementedError

