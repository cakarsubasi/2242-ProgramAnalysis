from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from .parser import JavaClass, JavaProgram
from pydoc import locate

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
    
    def next_counter(self):
        return Counter(self.method_name, self.counter + 1)

class StackElement:

    def __init__(self, local_variables, operational_stack, counter: Counter):
        self.local_variables: List[JavaValue] = local_variables
        self.operational_stack: List[JavaValue] = operational_stack
        self.counter: Counter = counter

class Interpreter:

    def __init__(self, java_class, method_name, method_args: List[JavaValue]):
        self.memory: Dict[str, JavaValue] = {}
        self.stack: List[StackElement] = [StackElement(method_args, [], Counter(method_name, 0))]
        self.java_class = java_class
        #self.method_name = method_name


    def run(self):
        for _ in range(10):
            element = self.stack[-1]
            method_bcode = self.java_class.get_method(element.counter.method_name)["code"]["bytecode"][element.counter.counter]
            if method_bcode["opr"] == "return":
                return perform_return(self, method_bcode, element)
            self.run_operation(method_bcode, element)

    def run_operation(self, operation, element):
        method = method_mapper[operation["opr"]]
        method(self, operation, element)


def perform_return(runner: Interpreter, opr: Dict, element: StackElement):
    type = opr["type"]
    if type == None:
        return None
    value = element.operational_stack[-1]
    return locate(type)(value)

def perform_push(runner: Interpreter, opr: Dict, element: StackElement):
    v = opr["value"]
    runner.stack.append(StackElement(element.local_variables, element.operational_stack + [v["value"]], element.counter.next_counter()))

def perform_load(runner: Interpreter, opr: Dict, element: StackElement):
    value = element.local_variables[opr["index"]]
    runner.stack.append(StackElement(element.local_variables, element.operational_stack + [value], element.counter.next_counter()))
    
method_mapper = {
    "push": perform_push,
    "return": perform_return,
    "load": perform_load
}

#runner = Interpreter(["add", "add"])
#runner.run()

def run_program(java_program: JavaProgram):
    # Ignore this for now
    raise NotImplementedError

def run_method(java_class: JavaClass, method_name: str, method_args: List[JavaValue], environment: Optional[JavaProgram]=None) -> JavaValue | JavaError:
    # This is the entry point, this function should create an
    # Interpreter instance, and then run it with the given
    # properties. It should raise an error
    # if it gets unexpected or inadequate arguments

    # The environment should allow referencing other classes

    interpreter = Interpreter(java_class, method_name, method_args)
    return interpreter.run()



