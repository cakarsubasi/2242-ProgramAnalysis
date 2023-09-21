from typing import Dict, List, Any, Optional
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
class BoolValue:
    value: bool

@dataclass
class ByteValue:
    # TODO: use a better byte
    value: int

@dataclass
class ArrayValue:
    value: List[Any]

@dataclass
class RefValue:
    # refvalue should contain a pointer
    # to another structure
    value: Any 
    # Also keep in mind that to emulate Java
    # behavior, we need reference counting
    # semantics but right now it is likely
    # simpler to just leak all memory

@dataclass
class ClassValue:
    class_name: str
    fields: Dict[str, RefValue]
    # strictly speaking, we do not have to store the method information

# JavaValue can be these things, but feel free to add more
JavaValue = IntValue | BoolValue | ByteValue | ShortValue | RefValue | None

#class Value:
#    def __init__(self, type_name: str, value: Any):
#        self.type_name = type_name
#        self.value = value

class JavaError:
    # Need a way of propagating errors
    # Probably best to discuss how to implement this before deciding on one
    pass

class Counter:

    def __init__(self, method_name: str, counter: int):
        self.method_name = method_name
        self.counter = counter

class StackElement:

    def __init__(self, counter: Counter):
        self.local_variables: List[JavaValue] = []
        self.operational_stack: List[JavaValue] = []
        self.counter: Counter = counter

class Interpreter:

    def __init__(self, json_program):
        self.memory: Dict[str, JavaValue] = {}
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

def run_program(java_program: JavaProgram):
    # Ignore this for now
    raise NotImplementedError

def run_method(java_class: JavaClass, method_name: str, method_args: Dict[str, JavaValue], environment: Optional[JavaProgram]=None) -> JavaValue | JavaError:
    # This is the entry point, this function should create an
    # Interpreter instance, and then run it with the given
    # properties. It should raise an error
    # if it gets unexpected or inadequate arguments

    # The environment should allow referencing other classes
    return IntValue(0)

