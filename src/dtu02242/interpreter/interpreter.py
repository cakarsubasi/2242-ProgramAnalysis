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

class Value:
    def __init__(self, value: Any, type_name: str = None):
        self.value = value
        if type_name is None:
            self.type_name = type(value).__name__ 
        else:
            self.type_name = type_name

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

    def __init__(self, local_variables: List[Value], operational_stack, counter: Counter):
        self.local_variables: List[Value] = local_variables
        self.operational_stack: List[Value] = operational_stack
        self.counter: Counter = counter

class Operation:
    def __init__(self, json_doc):
        self.offset: int = json_doc["offset"]
        self.opr: str = json_doc["opr"]
        self.type: str = json_doc["type"] if "type" in json_doc else None
        self.index: int = json_doc["index"] if "index" in json_doc else None
        self.operant: str = json_doc["operant"] if "operant" in json_doc else None
        self.value: Value = Value(json_doc["value"]["value"], json_doc["value"]["type"]) if "value" in json_doc else None
        self.condition: str = json_doc["condition"] if "condition" in json_doc else None
        self.target: int = json_doc["target"] if "target" in json_doc else None
        self.amount: int = json_doc["amount"] if "amount" in json_doc else None

    def get_name(self):
        if self.operant:
            return f"{self.opr}-{self.operant}"
        if self.condition:
            return f"{self.opr}-{self.condition}"
        return self.opr

class Interpreter:

    def __init__(self, java_class, method_name, method_args: List[Value]):
        self.memory: Dict[str, JavaValue] = {}
        self.stack: List[StackElement] = [StackElement(method_args, [], Counter(method_name, 0))]
        self.java_class = java_class
        #self.method_name = method_name

    def run(self):
        while True:
            element = self.stack[-1]
            operation = Operation(self.java_class.get_method(element.counter.method_name)["code"]["bytecode"][element.counter.counter])
            if operation.get_name() == "return":
                return perform_return(self, operation, element)
            self.run_operation(operation, element)

    def run_operation(self, operation: Operation, element: StackElement):
        method = method_mapper[operation.get_name()]
        method(self, operation, element)


def perform_return(runner: Interpreter, opr: Operation, element: StackElement):
    type = opr.type
    if type == None:
        return None
    value = element.operational_stack[-1].value
    return locate(type)(value)

def perform_push(runner: Interpreter, opr: Operation, element: StackElement):
    v = opr.value
    runner.stack.append(StackElement(element.local_variables, element.operational_stack + [v], element.counter.next_counter()))

def perform_load(runner: Interpreter, opr: Operation, element: StackElement):
    value = element.local_variables[opr.index]
    runner.stack.append(StackElement(element.local_variables, element.operational_stack + [value], element.counter.next_counter()))

def perform_add(runner: Interpreter, opr: Operation, element: StackElement):
    first = element.operational_stack[-2].value
    second = element.operational_stack[-1].value
    result = Value(first + second)
    runner.stack.append(StackElement(element.local_variables, element.operational_stack + [result], element.counter.next_counter()))

def perform_strictly_greater(runner: Interpreter, opr: Operation, element: StackElement):
    first = element.operational_stack[-2].value
    second = element.operational_stack[-1].value
    if first > second:
        next_counter = Counter(element.counter.method_name, opr.target)
        runner.stack.append(StackElement(element.local_variables, element.operational_stack, next_counter))
    else:
        runner.stack.append(StackElement(element.local_variables, element.operational_stack, element.counter.next_counter()))

def perform_greater_or_equal(runner: Interpreter, opr: Operation, element: StackElement):
    first = element.operational_stack[-2].value
    second = element.operational_stack[-1].value
    if first >= second:
        next_counter = Counter(element.counter.method_name, opr.target)
        runner.stack.append(StackElement(element.local_variables, element.operational_stack, next_counter))
    else:
        runner.stack.append(StackElement(element.local_variables, element.operational_stack, element.counter.next_counter()))

def perform_store(runner: Interpreter, opr: Operation, element: StackElement):
    value = element.operational_stack[-1]
    local_vars = [x for x in element.local_variables]
    if len(local_vars) <= opr.index:
        local_vars.append(value)
    else:
        local_vars[opr.index] = value
    runner.stack.append(StackElement(local_vars, element.operational_stack, element.counter.next_counter()))

def perform_less_than_or_equal_zero(runner: Interpreter, opr: Operation, element: StackElement):
    first = element.operational_stack[-1].value
    second = 0
    if first <= second:
        next_counter = Counter(element.counter.method_name, opr.target)
        runner.stack.append(StackElement(element.local_variables, element.operational_stack, next_counter))
    else:
        runner.stack.append(StackElement(element.local_variables, element.operational_stack, element.counter.next_counter()))

def perform_not_equal_zero(runner: Interpreter, opr: Operation, element: StackElement):
    first = element.operational_stack[-1].value
    second = 0
    if first != second:
        next_counter = Counter(element.counter.method_name, opr.target)
        runner.stack.append(StackElement(element.local_variables, element.operational_stack, next_counter))
    else:
        runner.stack.append(StackElement(element.local_variables, element.operational_stack, element.counter.next_counter()))

def perform_increment(runner: Interpreter, opr: Operation, element: StackElement):
    local_vars = [x for x in element.local_variables]
    value = element.local_variables[opr.index].value
    local_vars[opr.index] = Value(value + opr.amount)
    runner.stack.append(StackElement(local_vars, element.operational_stack, element.counter.next_counter()))

def perform_multiplication(runner: Interpreter, opr: Operation, element: StackElement):
    first = element.operational_stack[-2].value
    second = element.operational_stack[-1].value
    result = Value(first * second)
    runner.stack.append(StackElement(element.local_variables, element.operational_stack + [result], element.counter.next_counter()))

def perform_goto(runner: Interpreter, opr: Operation, element: StackElement):
    next_counter = Counter(element.counter.method_name, opr.target)
    runner.stack.append(StackElement(element.local_variables, element.operational_stack, next_counter))

def perform_array_load(runner: Interpreter, opr: Operation, element: StackElement):
    arr = element.operational_stack[-2].value
    index = element.operational_stack[-1].value
    value = Value(arr[index])
    runner.stack.append(StackElement(element.local_variables, element.operational_stack + [value], element.counter.next_counter()))

def perform_get(runner: Interpreter, opr: Operation, element: StackElement):
    # I am not sure what get does but I am guessing it returns 0 when it fails and 1 when it succeeds.
    # So we are just always going to assume that it works.
    runner.stack.append(StackElement(element.local_variables, element.operational_stack + [Value(1)], element.counter.next_counter()))

def perform_array_length(runner: Interpreter, opr: Operation, element: StackElement):
    arr = element.operational_stack[-1].value
    value = Value(len(arr))
    runner.stack.append(StackElement(element.local_variables, element.operational_stack + [value], element.counter.next_counter()))

method_mapper = {
    "push": perform_push,
    "return": perform_return,
    "load": perform_load,
    "binary-add": perform_add,
    "if-gt": perform_strictly_greater,
    "if-ge": perform_greater_or_equal,
    "store": perform_store,
    "ifz-le": perform_less_than_or_equal_zero,
    "ifz-ne": perform_not_equal_zero,
    "incr": perform_increment,
    "binary-mul": perform_multiplication,
    "goto": perform_goto,
    "array_load": perform_array_load,
    "arraylength": perform_array_length,
    "get": perform_get,
}

def run_program(java_program: JavaProgram):
    # Ignore this for now
    raise NotImplementedError

def run_method(java_class: JavaClass, method_name: str, method_args: List[JavaValue], environment: Optional[JavaProgram]=None) -> JavaValue | JavaError:
    # This is the entry point, this function should create an
    # Interpreter instance, and then run it with the given
    # properties. It should raise an error
    # if it gets unexpected or inadequate arguments

    # The environment should allow referencing other classes

    args = [Value(x) for x in method_args]
    interpreter = Interpreter(java_class, method_name, args)
    return interpreter.run()



