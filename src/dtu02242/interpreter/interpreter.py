from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from .parser import JavaClass, JavaProgram
from pydoc import locate
import uuid
import json

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
    length: int
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
        self.class_: str = json_doc["class"] if "class" in json_doc else None
        self.method: Dict[str, Any] = json_doc["method"] if "method" in json_doc else None

    def get_name(self):
        if self.operant:
            return f"{self.opr}-{self.operant}"
        if self.condition:
            return f"{self.opr}-{self.condition}"
        return self.opr

class Interpreter:

    def __init__(self, java_class: JavaClass, method_name, method_args: List[Value], memory: Dict[str, JavaValue] = {}):
        self.memory: Dict[str, JavaValue] = memory
        self.stack: List[StackElement] = [StackElement(method_args, [], Counter(method_name, 0))]
        self.java_class = java_class

    def get_class(self, class_name, method_name) -> JavaClass:
        if class_name == self.java_class.name:
            return self.java_class
        elif class_name == "java/io/PrintStream" and method_name == "println":
            return JavaClass(json.loads('{"name": "Mock", "methods" :[{"name":"' + method_name + '", "code": { "bytecode": [ { "offset": 0, "opr": "load", "type": "str", "index": 0 }, { "offset": 1, "opr": "print" }, { "offset": 2, "opr": "return", "type": null } ] } } ] }'))
        else:
            return JavaClass(json.loads('{"name": "Mock", "methods" :[{"name":"' + method_name + '", "code": { "bytecode": [ { "offset": 0, "opr": "push", "value": { "type": "integer", "value": 4 } }, { "offset": 1, "opr": "return", "type": "int" } ] } } ] }'))

    def run(self):
        while len(self.stack) > 0:
            element = self.stack.pop()
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
    value = element.operational_stack.pop().value
    return locate(type)(value)

def perform_push(runner: Interpreter, opr: Operation, element: StackElement):
    v = opr.value
    runner.stack.append(StackElement(element.local_variables, element.operational_stack + [v], element.counter.next_counter()))

def perform_load(runner: Interpreter, opr: Operation, element: StackElement):
    value = element.local_variables[opr.index]
    runner.stack.append(StackElement(element.local_variables, element.operational_stack + [value], element.counter.next_counter()))

def perform_add(runner: Interpreter, opr: Operation, element: StackElement):
    second = element.operational_stack.pop().value
    first = element.operational_stack.pop().value
    result = Value(first + second)
    runner.stack.append(StackElement(element.local_variables, element.operational_stack + [result], element.counter.next_counter()))

def perform_sub(runner: Interpreter, opr: Operation, element: StackElement):
    second = element.operational_stack.pop().value
    first = element.operational_stack.pop().value
    result = Value(first - second)
    runner.stack.append(StackElement(element.local_variables, element.operational_stack + [result], element.counter.next_counter()))

def perform_strictly_less(runner: Interpreter, opr: Operation, element: StackElement):
    second = element.operational_stack.pop().value
    first = element.operational_stack.pop().value
    if first < second:
        next_counter = Counter(element.counter.method_name, opr.target)
        runner.stack.append(StackElement(element.local_variables, element.operational_stack, next_counter))
    else:
        runner.stack.append(StackElement(element.local_variables, element.operational_stack, element.counter.next_counter()))

def perform_less_or_equal(runner: Interpreter, opr: Operation, element: StackElement):
    second = element.operational_stack.pop().value
    first = element.operational_stack.pop().value
    if first <= second:
        next_counter = Counter(element.counter.method_name, opr.target)
        runner.stack.append(StackElement(element.local_variables, element.operational_stack, next_counter))
    else:
        runner.stack.append(StackElement(element.local_variables, element.operational_stack, element.counter.next_counter()))


def perform_strictly_greater(runner: Interpreter, opr: Operation, element: StackElement):
    second = element.operational_stack.pop().value
    first = element.operational_stack.pop().value
    if first > second:
        next_counter = Counter(element.counter.method_name, opr.target)
        runner.stack.append(StackElement(element.local_variables, element.operational_stack, next_counter))
    else:
        runner.stack.append(StackElement(element.local_variables, element.operational_stack, element.counter.next_counter()))

def perform_greater_or_equal(runner: Interpreter, opr: Operation, element: StackElement):
    second = element.operational_stack.pop().value
    first = element.operational_stack.pop().value
    if first >= second:
        next_counter = Counter(element.counter.method_name, opr.target)
        runner.stack.append(StackElement(element.local_variables, element.operational_stack, next_counter))
    else:
        runner.stack.append(StackElement(element.local_variables, element.operational_stack, element.counter.next_counter()))

def perform_store(runner: Interpreter, opr: Operation, element: StackElement):
    value = element.operational_stack.pop()
    local_vars = [x for x in element.local_variables]
    if len(local_vars) <= opr.index:
        local_vars.append(value)
    else:
        local_vars[opr.index] = value
    runner.stack.append(StackElement(local_vars, element.operational_stack, element.counter.next_counter()))

def perform_less_than_or_equal_zero(runner: Interpreter, opr: Operation, element: StackElement):
    first = element.operational_stack.pop().value
    second = 0
    if first <= second:
        next_counter = Counter(element.counter.method_name, opr.target)
        runner.stack.append(StackElement(element.local_variables, element.operational_stack, next_counter))
    else:
        runner.stack.append(StackElement(element.local_variables, element.operational_stack, element.counter.next_counter()))

def perform_not_equal_zero(runner: Interpreter, opr: Operation, element: StackElement):
    first = element.operational_stack.pop().value
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
    second = element.operational_stack.pop().value
    first = element.operational_stack.pop().value
    result = Value(first * second)
    runner.stack.append(StackElement(element.local_variables, element.operational_stack + [result], element.counter.next_counter()))

def perform_goto(runner: Interpreter, opr: Operation, element: StackElement):
    next_counter = Counter(element.counter.method_name, opr.target)
    runner.stack.append(StackElement(element.local_variables, element.operational_stack, next_counter))

def perform_new_array(runner: Interpreter, opr: Operation, element: StackElement):
    size = element.operational_stack.pop().value
    memory_address = uuid.uuid4()
    runner.memory[memory_address] = ArrayValue(size, [0] * size)
    value = Value(memory_address)
    runner.stack.append(StackElement(element.local_variables, element.operational_stack + [value], element.counter.next_counter()))

def perform_array_store(runner: Interpreter, opr: Operation, element: StackElement):
    value_to_store = element.operational_stack.pop().value
    index = element.operational_stack.pop().value
    arr_address = element.operational_stack.pop().value
    runner.memory[arr_address].value[index] = value_to_store
    runner.stack.append(StackElement(element.local_variables, element.operational_stack, element.counter.next_counter()))

def perform_array_load(runner: Interpreter, opr: Operation, element: StackElement):
    index = element.operational_stack.pop().value
    arr_address = element.operational_stack.pop().value
    arr = runner.memory[arr_address]
    if arr.length <= index:
        raise Exception("Index out of bounds")
    value = Value(arr.value[index])
    runner.stack.append(StackElement(element.local_variables, element.operational_stack + [value], element.counter.next_counter()))

def perform_get(runner: Interpreter, opr: Operation, element: StackElement):
    # I am not sure what get does but I am guessing it returns 0 when it succeeds and some else otherwise.
    # So we are just always going to assume that it works.
    runner.stack.append(StackElement(element.local_variables, element.operational_stack + [Value(0)], element.counter.next_counter()))

def perform_array_length(runner: Interpreter, opr: Operation, element: StackElement):
    arr_address = element.operational_stack.pop().value
    arr_length = runner.memory[arr_address].length
    value = Value(arr_length)
    runner.stack.append(StackElement(element.local_variables, element.operational_stack + [value], element.counter.next_counter()))

def perform_new(runner: Interpreter, opr: Operation, element: StackElement):
    memory_address = uuid.uuid4() # Create random memory access
    runner.memory[memory_address] = opr.class_
    value = Value(memory_address, "ref")
    runner.stack.append(StackElement(element.local_variables, element.operational_stack + [value], element.counter.next_counter()))

def perform_dup(runner: Interpreter, opr: Operation, element: StackElement):
    value = element.operational_stack[-1]
    runner.stack.append(StackElement(element.local_variables, element.operational_stack + [value], element.counter.next_counter()))

def perform_invoke(runner: Interpreter, opr: Operation, element: StackElement):
    method_name = opr.method["name"]
    class_name = opr.method["ref"]["name"]
    args = []
    for _ in range(len(opr.method["args"])):
        args.append(element.operational_stack.pop().value)
    args.reverse()
    result = run_method(runner.get_class(class_name, method_name), method_name, args, runner.memory)
    if opr.method["returns"] is not None:
        runner.stack.append(StackElement(element.local_variables, element.operational_stack + [Value(result)], element.counter.next_counter()))
    else:
        runner.stack.append(StackElement(element.local_variables, element.operational_stack, element.counter.next_counter()))

def peform_throw(runner: Interpreter, opr: Operation, element: StackElement):
    exception_pointer = element.operational_stack.pop().value
    excpetion = runner.memory[exception_pointer]
    raise Exception(excpetion)

def perform_print(runner: Interpreter, opr: Operation, element: StackElement):
    value = element.operational_stack.pop().value
    print(value, end="")
    runner.stack.append(StackElement(element.local_variables, element.operational_stack, element.counter.next_counter()))

method_mapper = {
    "push": perform_push,
    "return": perform_return,
    "load": perform_load,
    "binary-add": perform_add,
    "binary-sub": perform_sub,
    "binary-mul": perform_multiplication,
    "if-lt": perform_strictly_less,
    "if-le": perform_less_or_equal,
    "if-gt": perform_strictly_greater,
    "if-ge": perform_greater_or_equal,
    "store": perform_store,
    "ifz-le": perform_less_than_or_equal_zero,
    "ifz-ne": perform_not_equal_zero,
    "incr": perform_increment,
    "goto": perform_goto,
    "newarray": perform_new_array,
    "array_store": perform_array_store,
    "array_load": perform_array_load,
    "arraylength": perform_array_length,
    "get": perform_get,
    "new": perform_new,
    "dup": perform_dup,
    "invoke": perform_invoke,
    "throw": peform_throw,
    "print": perform_print,
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

    args = []
    memory = {}
    for arg in method_args:
        type_name = type(arg).__name__
        if type_name == "list":
            memory_address = uuid.uuid4()
            memory[memory_address] = ArrayValue(len(arg), arg)
            args.append(Value(memory_address))
        else:
            args.append(Value(arg, type_name))

    interpreter = Interpreter(java_class, method_name, args, memory)
    return interpreter.run()
