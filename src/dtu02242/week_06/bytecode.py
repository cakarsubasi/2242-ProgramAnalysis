from .data_structures import Value, ArrayValue, AnalysisException
from typing import List, Dict, Any
import uuid

class IInterp:
    stack: Any
    memory: Any
    stdout: Any
    exceptions: List[AnalysisException]

    def get_class(self, class_name, method_name):
        raise NotImplementedError()

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
    def __init__(self, json_doc, value_creator):
        self.offset: int = json_doc["offset"]
        self.opr: str = json_doc["opr"]
        self.type: str = json_doc["type"] if "type" in json_doc else None
        self.index: int = json_doc["index"] if "index" in json_doc else None
        self.operant: str = json_doc["operant"] if "operant" in json_doc else None
        self.value: Value = value_creator(json_doc["value"]["value"], json_doc["value"]["type"]) if "value" in json_doc else None
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

class ByteCode:
    def __init__(self):
        self.method_mapper = {
    "push": self.perform_push,
    "return": self.perform_return,
    "load": self.perform_load,
    "binary-add": self.perform_add,
    "binary-sub": self.perform_sub,
    "binary-mul": self.perform_mul,
    "binary-div": self.perform_div,
    "if-lt": self.perform_strictly_less,
    "if-le": self.perform_less_or_equal,
    "if-gt": self.perform_strictly_greater,
    "if-ge": self.perform_greater_or_equal,
    "store": self.perform_store,
    "ifz-le": self.perform_less_than_or_equal_zero,
    "ifz-ne": self.perform_not_equal_zero,
    "incr": self.perform_increment,
    "goto": self.perform_goto,
    "newarray": self.perform_new_array,
    "array_store": self.perform_array_store,
    "array_load": self.perform_array_load,
    "arraylength": self.perform_array_length,
    "get": self.perform_get,
    "new": self.perform_new,
    "dup": self.perform_dup,
    "invoke": self.perform_invoke,
    "throw": self.peform_throw,
    "print": self.perform_print,
}
    def create_int_argument(self):
        # This is be implemented by all abstractions
        pass

    def create_float_argument(self):
        # This is be implemented by all abstractions
        pass

    def create_value(self, value: Any, type_name: str = "void") -> Value:
        return Value(value, type_name)
        
    def execute(self, instruction: str, runner: IInterp, opr: Operation, element: StackElement):
        return self.method_mapper[instruction](runner, opr, element)

    def perform_return(self, runner: IInterp, opr: Operation, element: StackElement):
        type = opr.type
        if type == None:
            return self.create_value(None)
        value = element.operational_stack.pop()
        return value

    def perform_push(self, runner: IInterp, opr: Operation, element: StackElement):
        v = opr.value
        runner.stack.append(StackElement(element.local_variables, element.operational_stack + [v], element.counter.next_counter()))

    def perform_load(self, runner: IInterp, opr: Operation, element: StackElement):
        value = element.local_variables[opr.index]
        runner.stack.append(StackElement(element.local_variables, element.operational_stack + [value], element.counter.next_counter()))

    def perform_add(self, runner: IInterp, opr: Operation, element: StackElement):
        second = element.operational_stack.pop()
        first = element.operational_stack.pop()
        result = first + second
        runner.stack.append(StackElement(element.local_variables, element.operational_stack + [result], element.counter.next_counter()))

    def perform_sub(self, runner: IInterp, opr: Operation, element: StackElement):
        second = element.operational_stack.pop()
        first = element.operational_stack.pop()
        result = first - second
        runner.stack.append(StackElement(element.local_variables, element.operational_stack + [result], element.counter.next_counter()))

    def perform_div(self, runner: IInterp, opr: Operation, element: StackElement):
        second = element.operational_stack.pop()
        first = element.operational_stack.pop()
        result = first / second
        runner.stack.append(StackElement(element.local_variables, element.operational_stack + [result], element.counter.next_counter()))
        
    def perform_mul(self, runner: IInterp, opr: Operation, element: StackElement):
        second = element.operational_stack.pop()
        first = element.operational_stack.pop()
        result = first * second
        runner.stack.append(StackElement(element.local_variables, element.operational_stack + [result], element.counter.next_counter()))

    def perform_strictly_less(self, runner: IInterp, opr: Operation, element: StackElement):
        second = element.operational_stack.pop()
        first = element.operational_stack.pop()
        if first < second:
            next_counter = Counter(element.counter.method_name, opr.target)
            runner.stack.append(StackElement(element.local_variables, element.operational_stack, next_counter))
        else:
            runner.stack.append(StackElement(element.local_variables, element.operational_stack, element.counter.next_counter()))

    def perform_less_or_equal(self, runner: IInterp, opr: Operation, element: StackElement):
        second = element.operational_stack.pop()
        first = element.operational_stack.pop()
        if first <= second:
            next_counter = Counter(element.counter.method_name, opr.target)
            runner.stack.append(StackElement(element.local_variables, element.operational_stack, next_counter))
        else:
            runner.stack.append(StackElement(element.local_variables, element.operational_stack, element.counter.next_counter()))


    def perform_strictly_greater(self, runner: IInterp, opr: Operation, element: StackElement):
        second = element.operational_stack.pop()
        first = element.operational_stack.pop()
        if first > second:
            next_counter = Counter(element.counter.method_name, opr.target)
            runner.stack.append(StackElement(element.local_variables, element.operational_stack, next_counter))
        else:
            runner.stack.append(StackElement(element.local_variables, element.operational_stack, element.counter.next_counter()))

    def perform_greater_or_equal(self, runner: IInterp, opr: Operation, element: StackElement):
        second = element.operational_stack.pop()
        first = element.operational_stack.pop()
        if first >= second:
            next_counter = Counter(element.counter.method_name, opr.target)
            runner.stack.append(StackElement(element.local_variables, element.operational_stack, next_counter))
        else:
            runner.stack.append(StackElement(element.local_variables, element.operational_stack, element.counter.next_counter()))

    def perform_store(self, runner: IInterp, opr: Operation, element: StackElement):
        value = element.operational_stack.pop()
        local_vars = [x for x in element.local_variables]
        if len(local_vars) <= opr.index:
            local_vars.append(value)
        else:
            local_vars[opr.index] = value
        runner.stack.append(StackElement(local_vars, element.operational_stack, element.counter.next_counter()))

    def perform_less_than_or_equal_zero(self, runner: IInterp, opr: Operation, element: StackElement):
        first = element.operational_stack.pop()
        second = self.create_value(0, 'integer')
        if first <= second:
            next_counter = Counter(element.counter.method_name, opr.target)
            runner.stack.append(StackElement(element.local_variables, element.operational_stack, next_counter))
        else:
            runner.stack.append(StackElement(element.local_variables, element.operational_stack, element.counter.next_counter()))

    def perform_not_equal_zero(self, runner: IInterp, opr: Operation, element: StackElement):
        first = element.operational_stack.pop()
        second = self.create_value(0, 'integer')
        if first != second:
            next_counter = Counter(element.counter.method_name, opr.target)
            runner.stack.append(StackElement(element.local_variables, element.operational_stack, next_counter))
        else:
            runner.stack.append(StackElement(element.local_variables, element.operational_stack, element.counter.next_counter()))

    def perform_increment(self, runner: IInterp, opr: Operation, element: StackElement):
        local_vars = [x for x in element.local_variables]
        value = element.local_variables[opr.index]
        local_vars[opr.index] = value + self.create_value(opr.amount)
        runner.stack.append(StackElement(local_vars, element.operational_stack, element.counter.next_counter()))

    def perform_goto(self, runner: IInterp, opr: Operation, element: StackElement):
        next_counter = Counter(element.counter.method_name, opr.target)
        runner.stack.append(StackElement(element.local_variables, element.operational_stack, next_counter))

    def perform_new_array(self, runner: IInterp, opr: Operation, element: StackElement):
        size = element.operational_stack.pop().get_value()
        memory_address = uuid.uuid4()
        runner.memory[memory_address] = ArrayValue(size, self.create_value(0))
        value = self.create_value(memory_address)
        runner.stack.append(StackElement(element.local_variables, element.operational_stack + [value], element.counter.next_counter()))

    def perform_array_store(self, runner: IInterp, opr: Operation, element: StackElement):
        value_to_store = element.operational_stack.pop()
        index = element.operational_stack.pop().get_value()
        arr_address = element.operational_stack.pop().get_value()
        runner.memory[arr_address][index] = value_to_store
        runner.stack.append(StackElement(element.local_variables, element.operational_stack, element.counter.next_counter()))

    def perform_array_load(self, runner: IInterp, opr: Operation, element: StackElement):
        index = element.operational_stack.pop().get_value()
        arr_address = element.operational_stack.pop().get_value()
        arr: ArrayValue = runner.memory[arr_address]
        if arr.get_length() <= index:
            raise Exception("Index out of bounds")
        value = arr[index]
        runner.stack.append(StackElement(element.local_variables, element.operational_stack + [value], element.counter.next_counter()))

    def perform_get(self, runner: IInterp, opr: Operation, element: StackElement):
        # I am not sure what get does but I am guessing it returns 0 when it succeeds and some else otherwise.
        # So we are just always going to assume that it works.
        runner.stack.append(StackElement(element.local_variables, element.operational_stack + [self.create_value(0, "integer")], element.counter.next_counter()))

    def perform_array_length(self, runner: IInterp, opr: Operation, element: StackElement):
        arr_address = element.operational_stack.pop().get_value()
        arr_length = runner.memory[arr_address].get_length()
        value = self.create_value(arr_length)
        runner.stack.append(StackElement(element.local_variables, element.operational_stack + [value], element.counter.next_counter()))

    def perform_new(self, runner: IInterp, opr: Operation, element: StackElement):
        memory_address = uuid.uuid4() # Create random memory access
        runner.memory[memory_address] = opr.class_
        value = self.create_value(memory_address, "ref")
        runner.stack.append(StackElement(element.local_variables, element.operational_stack + [value], element.counter.next_counter()))

    def perform_dup(self, runner: IInterp, opr: Operation, element: StackElement):
        value = element.operational_stack[-1]
        runner.stack.append(StackElement(element.local_variables, element.operational_stack + [value], element.counter.next_counter()))

    def perform_invoke(self, runner: IInterp, opr: Operation, element: StackElement):
        raise NotImplementedError("All state that the bytecode interpreter stores should \
                                  not be a part of the program itself, therefore this method \
                                  should not spawn another Interpreter instance \
                                  ")


    def peform_throw(self, runner: IInterp, opr: Operation, element: StackElement):
        exception_pointer = element.operational_stack.pop()
        exception = runner.memory[exception_pointer.get_value()]
        raise Exception(exception)

    def perform_print(self, runner: IInterp, opr: Operation, element: StackElement):
        value = element.operational_stack.pop()
        runner.stdout.push(str(value))
        print(value, end="")
        runner.stack.append(StackElement(element.local_variables, element.operational_stack, element.counter.next_counter()))

class ByteCodeAbstraction(ByteCode):
    # Add fields here to record state
    def __init__(self):
        super().__init__()

    # Override methods here to alter program behavior
    