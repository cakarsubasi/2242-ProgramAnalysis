from typing import Dict, List, Any, Optional

from dtu02242.week_06.data_structures import ArrayValue, OutputBuffer, Value
from .parser import JavaClass, JavaProgram
from .bytecode import IInterp
from .bytecode import ByteCode, StackElement, Counter, Operation
from pydoc import locate
import uuid
import json

def perform_invoke(runner: IInterp, opr: Operation, element: StackElement):
    pass
    method_name = opr.method["name"]
    class_name = opr.method["ref"]["name"]
    args = []
    for _ in range(len(opr.method["args"])):
        args.append(element.operational_stack.pop())
    args.reverse()
    result = run_method(runner.get_class(class_name, method_name), method_name, args, runner.memory, runner.stdout)
    if opr.method["returns"] is not None:
        runner.stack.append(StackElement(element.local_variables, element.operational_stack + [result], element.counter.next_counter()))
    else:
        runner.stack.append(StackElement(element.local_variables, element.operational_stack, element.counter.next_counter()))

class Interpreter(IInterp):

    def __init__(self, java_class: JavaClass, 
                 method_name: str, 
                 method_args: List[Value], 
                 memory: Dict[str, Value] = {},
                 bytecode_interpreter = ByteCode(),
                 stdout: OutputBuffer=OutputBuffer()):
        self.memory: Dict[str, Value] = memory
        self.stack: List[StackElement] = [StackElement(method_args, [], Counter(method_name, 0))]
        self.java_class = java_class
        self.stdout = stdout
        self.bytecode_interpreter = bytecode_interpreter

    def get_class(self, class_name, method_name) -> JavaClass:
        if class_name == self.java_class.name:
            return self.java_class
        elif class_name == "java/io/PrintStream" and method_name == "println":
            return JavaClass(json.loads('{"name": "Mock", "methods" :[{"name":"' + method_name + '", "code": { "bytecode": [ { "offset": 0, "opr": "load", "type": "str", "index": 0 }, { "offset": 1, "opr": "print" }, { "offset": 2, "opr": "return", "type": null } ] } } ] }'))
        else:
            return JavaClass(json.loads('{"name": "Mock", "methods" :[{"name":"' + method_name + '", "code": { "bytecode": [ { "offset": 0, "opr": "push", "value": { "type": "integer", "value": 4 } }, { "offset": 1, "opr": "return", "type": "int" } ] } } ] }'))

    def run(self) -> Value:
        while len(self.stack) > 0:
            element = self.stack.pop()
            operation = Operation(self.java_class.get_method(element.counter.method_name)["code"]["bytecode"][element.counter.counter])
            result = self.run_operation(operation, element)
            if operation.get_name() == "return":
                return result
        raise Exception("Raised end without breaking")

    def run_operation(self, operation: Operation, element: StackElement) -> Value | None:
        operation_name = operation.get_name()
        method = self.bytecode_interpreter.method_mapper[operation_name]

        match operation_name:
            case "invoke":
                return perform_invoke(self, operation, element)
            case "return":
                return method(self, operation, element)
            case _:
                method(self, operation, element)

def run_program(java_program: JavaProgram):
    # Ignore this for now
    raise NotImplementedError

def run_method(java_class: JavaClass, 
               method_name: str, 
               method_args: List[Value],  
               environment: Optional[Dict[Any, Any]]=None, 
               stdout: OutputBuffer=OutputBuffer()) -> Value:
    # This is the entry point, this function should create an
    # Interpreter instance, and then run it with the given
    # properties. It should raise an error
    # if it gets unexpected or inadequate arguments

    # The environment should allow referencing other classes
    #method_args = wrap(method_args)

    args = []
    memory = {}
    for arg in method_args:
        #type_name = type(arg).__name__
        if arg.__class__ is ArrayValue:
            memory_address = uuid.uuid4()
            memory[memory_address] = arg # ArrayValue(arg)
            args.append(Value(memory_address))
        else:
            args.append(arg)

    interpreter = Interpreter(java_class=java_class, 
                              method_name=method_name, 
                              method_args=args, 
                              memory=memory, 
                              stdout=stdout)
    return interpreter.run()
