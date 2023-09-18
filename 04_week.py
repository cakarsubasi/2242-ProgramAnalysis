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

    def __init__(self):
        self.memory: Dict[str, Value] = {}
        self.stack = List[StackElement]

    def run(self):
        pass

    def step(self):
        pass

    def pop(self):
        pass