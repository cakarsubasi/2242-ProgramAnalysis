from typing import Dict, List, Any, Optional
from .parser import JavaClass, JavaProgram, JsonDict
import uuid
import json
from enum import Enum
from copy import deepcopy


class Counter:
    def __init__(self, method_name: str, counter: int):
        self.method_name = method_name
        self.counter = counter
    
    def next_counter(self):
        return Counter(self.method_name, self.counter + 1)

class StackElement:
    def __init__(self, local_variables: List[Any], operational_stack, counter: Counter):
        self.local_variables: List['MinusZeroPlusValue'] = local_variables
        self.operational_stack: List['MinusZeroPlusValue'] = operational_stack
        self.counter: Counter = counter
    
    def to_state_description(self):
        result = f"counter=({self.counter.method_name}-{self.counter.counter})"
        result += "-locals=("
        for l in self.local_variables:
            result += f"-{l.reference}-{l.plus}-{l.zero}-{l.minus}"
        result += ")-stack=("
        for s in self.operational_stack:
            result += f"-{s.reference}-{s.plus}-{s.zero}-{s.minus}"
        result += ")"
        return result
        
class Operation:
    def __init__(self, json_doc):
        self.offset: int = json_doc["offset"]
        self.opr: str = json_doc["opr"]
        self.type: str = json_doc["type"] if "type" in json_doc else None
        self.index: int = json_doc["index"] if "index" in json_doc else None
        self.operant: str = json_doc["operant"] if "operant" in json_doc else None
        self.value: Any = MinusZeroPlusValue(json_doc["value"]["value"]) if "value" in json_doc else None
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

class MinusZeroPlusValue:
    def __init__(self, number=None, reference=None):
        self.reference = reference
        if number is None:
            self.minus = True
            self.zero = True
            self.plus = True
        elif number < 0:
            self.minus = True
            self.zero = False
            self.plus = False
        elif number == 0:
            self.minus = False
            self.zero = True
            self.plus = False
        else:
            self.minus = False
            self.zero = False
            self.plus = True

class AnalysisResult(Enum):
    No = 0
    Maybe = 1
    AssertionError = 2
    IndexOutOfBoundsExecption = 3
    ArithmeticException = 4
    NullPointerException = 5
    UnsupportedOperationException = 6

class Analyzer():
    java_program: JavaProgram
    memory: Dict[uuid.UUID, Any]
    exceptions: List[AnalysisResult]

    def __init__(self, 
                 java_program: JavaProgram | JavaClass, 
                 memory: Dict[uuid.UUID, Any] = {},
                 abstraction: Any = None):
        self.memory = memory
        self.stack: List[StackElement] = []
        self.abstraction = abstraction
        self.exceptions = []
        self.seen_states = set()

        if type(java_program) is JavaProgram:
            self.java_program = java_program
        elif type(java_program) is JavaClass:
            self.java_program = JavaProgram([java_program])
        else:
            raise Exception("Unexpected type as JavaProgram")

    def get_class(self, class_name, method_name) -> JavaClass:
        class_maybe = self.java_program.get_class(class_name=class_name)
        if class_maybe is not None:
            return class_maybe
        else:
            return JavaClass(json.loads('{"name": "Mock", "methods" :[{"name":"' + method_name + '", "code": { "bytecode": [ { "offset": 0, "opr": "push", "value": { "type": "integer", "value": 4 } }, { "offset": 1, "opr": "return", "type": "int" } ] } } ] }'))

    def run(self, class_name: str, method_name: str, method_args: List[Any]) -> Any:
        self.stack.append(StackElement(method_args, [], Counter(method_name, 0)))
        saw_fixed_point = False
        while len(self.stack) > 0:
            element = self.stack.pop()
            state_description = element.to_state_description()
            if state_description in self.seen_states:
                saw_fixed_point = True
                continue
            self.seen_states.add(state_description)
            operation = Operation(self.get_class(class_name, method_name).get_method(element.counter.method_name)["code"]["bytecode"][element.counter.counter])
            self.run_operation(operation, element)
            if AnalysisResult.ArithmeticException in self.exceptions:
                return self.exceptions
        if self.exceptions:
            return self.exceptions
        if saw_fixed_point:
            return [AnalysisResult.Maybe]
        return [AnalysisResult.No] 

    def run_operation(self, operation: Operation, element: StackElement) -> Any | None:
        operation_name = operation.get_name()

        match operation_name:
            case "return":
                return self.abstraction.execute(operation_name, self, operation, element)
            case _:
                self.abstraction.execute(operation_name, self, operation, element)

class MinusZeroPlus:

    def __init__(self):
        self.method_mapper = {
        "binary-div": self.perform_division,
        "binary-sub": self.perform_sub,
        "binary-add": self.perform_add,
        "get": self.perform_get,
        "goto": self.perform_goto,
        "if-ge": self.perform_greater_or_equal,
        "if-gt": self.perform_strictly_greater,
        "if-lt": self.perform_strictly_less,
        "if-le": self.perform_less_or_equal,
        "ifz-gt": self.perform_greater_than_zero,
        "ifz-eq": self.perform_equal_zero,
        "ifz-le": self.perform_less_than_or_equal_zero,
        "ifz-lt": self.perform_less_than_zero,
        "ifz-ne": self.perform_not_equal_zero,
        "incr": self.perform_increment,
        "load": self.perform_load,
        "negate": self.perform_negate,
        "new": self.perform_new,
        "push": self.perform_push,
        "return": self.perform_return,
        "store": self.perform_store,
    }

    def execute(self, operation_name: str, analyzer: Analyzer, operation: Operation, element: StackElement):
        return self.method_mapper[operation_name](analyzer, operation, element)
    
    def create_next_element(self, element: StackElement, new_locals: List[Any], new_operation_stack_elements: List[Any]) -> StackElement:
        locals = deepcopy(element.local_variables) + new_locals
        operational_stack = deepcopy(element.operational_stack) + new_operation_stack_elements
        counter = element.counter.next_counter()
        return StackElement(locals, operational_stack, counter)
    
    def perform_get(self, runner: Analyzer, opr: Operation, element: StackElement):
        # I am not sure what get does but I am guessing it returns 0 when it succeeds and some else otherwise.
        # So we are just always going to assume that it works.
        runner.stack.append(self.create_next_element(element, [], [MinusZeroPlusValue(0)]))

    def perform_goto(self, runner: Analyzer, opr: Operation, element: StackElement):
        next_element = self.create_next_element(element, [], [])
        next_element.counter.counter = opr.target
        runner.stack.append(next_element)

    def perform_new(self, runner: Analyzer, opr: Operation, element: StackElement):
        if opr.class_ == "java/lang/AssertionError":
            runner.exceptions.append(AnalysisResult.AssertionError)
        else:
            raise Exception("Unhandled type for new keyword")

    def perform_push(self, runner: Analyzer, opr: Operation, element: StackElement):
        v = opr.value
        runner.stack.append(self.create_next_element(element, [], [v]))
    
    def assertion_was_true(self, runner: Analyzer, opr: Operation, element: StackElement, first: MinusZeroPlusValue, value: int):
        next_element = self.create_next_element(element, [], [])
        next_element.counter.counter = opr.target
        if first.reference is not None:
            next_element.local_variables[first.reference] = MinusZeroPlusValue(value)
        runner.stack.append(next_element)

    def assertion_was_false(self, runner: Analyzer, opr: Operation, element: StackElement, first: MinusZeroPlusValue, value: int):
        next_element = self.create_next_element(element, [], [])
        if first.reference is not None:
            next_element.local_variables[first.reference] = MinusZeroPlusValue(value)
        runner.stack.append(next_element)
        
    def assertion_was_true_pair(self, runner: Analyzer, opr: Operation, element: StackElement, first: MinusZeroPlusValue, first_value: int, second: MinusZeroPlusValue, sec_value: int):
        next_element = self.create_next_element(element, [], [])
        next_element.counter.counter = opr.target
        if first.reference is not None:
            next_element.local_variables[first.reference] = MinusZeroPlusValue(first_value)
        if second.reference is not None:
            next_element.local_variables[second.reference] = MinusZeroPlusValue(sec_value)
        runner.stack.append(next_element)

    def assertion_was_false_pair(self, runner: Analyzer, opr: Operation, element: StackElement, first: MinusZeroPlusValue, first_value: int, second: MinusZeroPlusValue, sec_value: int):
        next_element = self.create_next_element(element, [], [])
        if first.reference is not None:
            next_element.local_variables[first.reference] = MinusZeroPlusValue(first_value)
        if second.reference is not None:
            next_element.local_variables[second.reference] = MinusZeroPlusValue(sec_value)
        runner.stack.append(next_element)
    
    def perform_strictly_less(self, runner: Analyzer, opr: Operation, element: StackElement):
        second = element.operational_stack.pop()
        first = element.operational_stack.pop()
        if first.minus:
            self.assertion_was_true(runner, opr, element, first, -1)
        if first.zero:
            if second.plus:
                self.assertion_was_true_pair(runner, opr, element, first, 0, second, 1)
            if second.zero:
                self.assertion_was_false_pair(runner, opr, element, first, 0, second, 0)
            if second.minus:
                self.assertion_was_false_pair(runner, opr, element, first, 0, second, -1)
        if first.plus:
            self.assertion_was_false(runner, opr, element, first, 1)
    
    def perform_less_or_equal(self, runner: Analyzer, opr: Operation, element: StackElement):
        second = element.operational_stack.pop()
        first = element.operational_stack.pop()
        if first.minus:
            self.assertion_was_true(runner, opr, element, first, -1)
        if first.zero:
            if second.plus:
                self.assertion_was_true_pair(runner, opr, element, first, 0, second, 1)
            if second.zero:
                self.assertion_was_true_pair(runner, opr, element, first, 0, second, 0)
            if second.minus:
                self.assertion_was_false_pair(runner, opr, element, first, 0, second, -1)
        if first.plus:
            if second.plus:
                self.assertion_was_true_pair(runner, opr, element, first, 1, second, 1)
            if second.zero:
                self.assertion_was_false_pair(runner, opr, element, first, 1, second, 0)
            if second.minus:
                self.assertion_was_false_pair(runner, opr, element, first, 1, second, -1)

    def perform_greater_or_equal(self, runner: Analyzer, opr: Operation, element: StackElement):
        second = element.operational_stack.pop()
        first = element.operational_stack.pop()
        if first.plus:
            self.assertion_was_true(runner, opr, element, first, 1)
        if first.zero:
            if second.zero:
                self.assertion_was_true_pair(runner, opr, element, first, 0, second, 0)
            if second.minus:
                self.assertion_was_true_pair(runner, opr, element, first, 0, second, -1)
            if second.plus:
                self.assertion_was_false_pair(runner, opr, element, first, 0, second, 1)
        if first.minus:
            if second.minus:
                self.assertion_was_true_pair(runner, opr, element, first, -1, second, -1)
            if second.zero:
                self.assertion_was_false_pair(runner, opr, element, first, -1, second, 0)
            if second.plus:
                self.assertion_was_false_pair(runner, opr, element, first, -1, second, 1)

    def perform_strictly_greater(self, runner: Analyzer, opr: Operation, element: StackElement):
        second = element.operational_stack.pop()
        first = element.operational_stack.pop()
        if first.plus:
            self.assertion_was_true(runner, opr, element, first, 1)
        if first.zero:
            if second.minus:
                self.assertion_was_true_pair(runner, opr, element, first, 0, second, -1)
            if second.plus:
                self.assertion_was_false_pair(runner, opr, element, first, 0, second, 1)
            if second.zero:
                self.assertion_was_false_pair(runner, opr, element, first, 0, second, 0)
        if first.minus:
            if second.minus:
                self.assertion_was_true_pair(runner, opr, element, first, -1, second, -1)
            if second.zero:
                self.assertion_was_false_pair(runner, opr, element, first, -1, second, 0)
            if second.plus:
                self.assertion_was_false_pair(runner, opr, element, first, -1, second, 1)

    def perform_greater_than_zero(self, runner: Analyzer, opr: Operation, element: StackElement):
        first = element.operational_stack.pop()
        if first.plus:
            self.assertion_was_true(runner, opr, element, first, 1)
        if first.zero:
            self.assertion_was_false(runner, opr, element, first, 0)
        if first.minus:
            self.assertion_was_false(runner, opr, element, first, -1)
  
    def perform_less_than_or_equal_zero(self, runner: Analyzer, opr: Operation, element: StackElement):
        first = element.operational_stack.pop()
        if first.zero:
            self.assertion_was_true(runner, opr, element, first, 0)
        if first.minus:
            self.assertion_was_true(runner, opr, element, first, -1)
        if first.plus:
            self.assertion_was_false(runner, opr, element, first, 1)
      
    def perform_equal_zero(self, runner: Analyzer, opr: Operation, element: StackElement):
        first = element.operational_stack.pop()
        if first.zero:
            self.assertion_was_true(runner, opr, element, first, 0)
        if first.minus:
            self.assertion_was_false(runner, opr, element, first, -1)
        if first.plus:
            self.assertion_was_false(runner, opr, element, first, 1)
      
    def perform_less_than_zero(self, runner: Analyzer, opr: Operation, element: StackElement):
        first = element.operational_stack.pop()
        if first.minus:
            self.assertion_was_true(runner, opr, element, first, -1)
        if first.zero:
            self.assertion_was_false(runner, opr, element, first, 0)
        if first.plus:
            self.assertion_was_false(runner, opr, element, first, 1)

    def perform_not_equal_zero(self, runner: Analyzer, opr: Operation, element: StackElement):
        first = element.operational_stack.pop()
        if first.plus:
            self.assertion_was_true(runner, opr, element, first, 1)
        if first.minus:
            self.assertion_was_true(runner, opr, element, first, -1)
        if first.zero:
            self.assertion_was_false(runner, opr, element, first, 0)
    
    def perform_division(self, runner: Analyzer, opr: Operation, element: StackElement):
        second = element.operational_stack.pop()
        first = element.operational_stack.pop()
        if second.zero:
            runner.exceptions.append(AnalysisResult.ArithmeticException)
            return
        if first.zero:
            runner.stack.append(self.create_next_element(element, [], [MinusZeroPlusValue(0)]))
        if first.minus and second.minus:
            runner.stack.append(self.create_next_element(element, [], [MinusZeroPlusValue(1)]))
        if (first.minus and second.plus) or (second.plus and first.minus):
            runner.stack.append(self.create_next_element(element, [], [MinusZeroPlusValue(-1)]))
        if first.plus and second.plus:
            runner.stack.append(self.create_next_element(element, [], [MinusZeroPlusValue(1)]))
    
    def perform_sub(self, runner: Analyzer, opr: Operation, element: StackElement):
        second = element.operational_stack.pop()
        first = element.operational_stack.pop()
        if second.plus:
            if first.minus:
                runner.stack.append(self.create_next_element(element, [], [MinusZeroPlusValue(-1)]))
            if first.zero:
                runner.stack.append(self.create_next_element(element, [], [MinusZeroPlusValue(-1)]))
            if first.plus:
                runner.stack.append(self.create_next_element(element, [], [MinusZeroPlusValue()]))
        if second.zero:
            result = deepcopy(first)
            result.reference = None
            runner.stack.append(self.create_next_element(element, [], [result]))
        if second.minus:
            if first.minus:
                runner.stack.append(self.create_next_element(element, [], [MinusZeroPlusValue()]))
            if first.zero:
                runner.stack.append(self.create_next_element(element, [], [MinusZeroPlusValue(1)]))
            if first.plus:
                runner.stack.append(self.create_next_element(element, [], [MinusZeroPlusValue(1)]))
    
    def perform_add(self, runner: Analyzer, opr: Operation, element: StackElement):
        second = element.operational_stack.pop()
        first = element.operational_stack.pop()
        if second.plus:
            if first.minus:
                runner.stack.append(self.create_next_element(element, [], [MinusZeroPlusValue()]))
            if first.zero:
                runner.stack.append(self.create_next_element(element, [], [MinusZeroPlusValue(1)]))
            if first.plus:
                runner.stack.append(self.create_next_element(element, [], [MinusZeroPlusValue(1)]))
        if second.zero:
            result = deepcopy(first)
            result.reference = None
            runner.stack.append(self.create_next_element(element, [], [result]))
        if second.minus:
            if first.minus:
                runner.stack.append(self.create_next_element(element, [], [MinusZeroPlusValue(-1)]))
            if first.zero:
                runner.stack.append(self.create_next_element(element, [], [MinusZeroPlusValue(-1)]))
            if first.plus:
                runner.stack.append(self.create_next_element(element, [], [MinusZeroPlusValue()]))
    
    def perform_increment(self, runner: Analyzer, opr: Operation, element: StackElement):
        variable = element.local_variables[opr.index]
        if opr.amount == 0:
            next_element = self.create_next_element(element, [], [])
            runner.stack.append(next_element)
        if variable.plus:
            next_element = self.create_next_element(element, [], [])
            if opr.amount < 0:
                next_element.local_variables[opr.index].plus = True
                next_element.local_variables[opr.index].zero = True
                if opr.amount == -1:
                    next_element.local_variables[opr.index].minus = False
                else:
                    next_element.local_variables[opr.index].minus = True
            else:
                next_element.local_variables[opr.index].plus = True
                next_element.local_variables[opr.index].zero = False
                next_element.local_variables[opr.index].minus = False
            runner.stack.append(next_element)
        if variable.zero:
            next_element = self.create_next_element(element, [], [])
            if opr.amount < 0:
                next_element.local_variables[opr.index].plus = False
                next_element.local_variables[opr.index].zero = False
                next_element.local_variables[opr.index].minus = True
            else:
                next_element.local_variables[opr.index].plus = True
                next_element.local_variables[opr.index].zero = False
                next_element.local_variables[opr.index].minus = False
            runner.stack.append(next_element)
        if variable.minus:
            next_element = self.create_next_element(element, [], [])
            if opr.amount < 0:
                next_element.local_variables[opr.index].plus = False
                next_element.local_variables[opr.index].zero = False
                next_element.local_variables[opr.index].minus = True
            else:
                next_element.local_variables[opr.index].zero = True
                next_element.local_variables[opr.index].minus = True
                if opr.amount == 1:
                    next_element.local_variables[opr.index].plus = False
                else:
                    next_element.local_variables[opr.index].plus = True
            runner.stack.append(next_element)

    def perform_negate(self, runner: Analyzer, opr: Operation, element: StackElement):
        variable = element.operational_stack.pop()
        if variable.plus: 
            next_element = self.create_next_element(element, [], [])
            next_element.local_variables[variable.reference].plus = False
            next_element.local_variables[variable.reference].minus = True
            next_element.operational_stack.append(next_element.local_variables[variable.reference])
            runner.stack.append(next_element)
        if variable.zero:
            next_element = self.create_next_element(element, [], [])
            next_element.operational_stack.append(next_element.local_variables[variable.reference])
            runner.stack.append(next_element)
        if variable.minus:
            next_element = self.create_next_element(element, [], [])
            next_element.local_variables[variable.reference].plus = True
            next_element.local_variables[variable.reference].minus = False
            next_element.operational_stack.append(next_element.local_variables[variable.reference])
            runner.stack.append(next_element)


    def perform_load(self, runner: Analyzer, opr: Operation, element: StackElement):
        value = element.local_variables[opr.index]
        value.reference = opr.index
        runner.stack.append(self.create_next_element(element, [], [value]))

    def perform_store(self, runner: Analyzer, opr: Operation, element: StackElement):
        value = element.operational_stack.pop()
        next_element = self.create_next_element(element, [], [])
        if len(next_element.local_variables) <= opr.index:
            next_element.local_variables.append(value)
        else:
            next_element.local_variables[opr.index] = value
        runner.stack.append(next_element)
    
    def perform_return(self, runner: Analyzer, opr: Operation, element: StackElement):
        type = opr.type
        if type == None:
            return None
        value = element.operational_stack.pop()
        return value


def run_method_analysis(java_class: JavaClass,
                        method_name: str) -> AnalysisResult:
    
    args = []
    memory = {}
    method = java_class.get_method(method_name)
    for arg in method["params"]:
        if arg["type"]["base"] in ["int", "float"]:
            arg = MinusZeroPlusValue(None)
        else:
            raise Exception(f"Unknown type {arg['type']['base']}")
        args.append(arg)

    interpreter = Analyzer(java_program=java_class, 
                              memory=memory,
                              abstraction=MinusZeroPlus())
    return interpreter.run(java_class.name, method_name, args)