from typing import Dict, List

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

class Value:

    def __init__(self, type_name, value):
        self.type_name = type_name
        self.value = value

class Counter:

    def __init__(self, method_name, counter):
        self.method_name = method_name
        self.counter = counter

class StackElement:

    def __init__(self, counter):
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

runner = Interpreter(["add", "add"])
runner.run()