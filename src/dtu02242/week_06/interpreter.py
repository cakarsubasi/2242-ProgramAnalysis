from typing import Dict, List, Any, Tuple, Optional

from .range_abstraction import RangeAbstraction, RangeValue
from .data_structures import ArrayValue, OutputBuffer, Value, AnalysisException
from .parser import JavaClass, JavaProgram, JsonDict
from .bytecode import IInterp
from .bytecode import ByteCode, StackElement, Counter, Operation
import uuid
import json

StackFrame = List[StackElement]

class Interpreter(IInterp):
    java_program: JavaProgram
    bytecode_interpreter: ByteCode
    memory: Dict[uuid.UUID, Value]
    stack_of_stacks: List[StackFrame] = []
    memory: Dict[uuid.UUID, Value] = {}
    stdout: OutputBuffer
    exceptions: List[AnalysisException] 

    def __init__(self, 
                 java_program: JavaProgram | JavaClass, 
                 memory: Dict[uuid.UUID, Value] = {},
                 bytecode_interpreter = ByteCode(),
                 stdout: OutputBuffer=OutputBuffer()):
        self.memory = memory
        self.stack: List[StackElement] = []
        self.stack_of_stacks.append(self.stack)
        self.exceptions = []

        if type(java_program) is JavaProgram:
            self.java_program = java_program
        elif type(java_program) is JavaClass:
            self.java_program = JavaProgram([java_program])
        else:
            raise Exception("Unexpected type as JavaProgram")
        self.stdout = stdout
        self.bytecode_interpreter = bytecode_interpreter

    def get_class(self, class_name, method_name) -> JavaClass:
        class_maybe = self.java_program.get_class(class_name=class_name)
        if class_maybe is not None:
            return class_maybe
        elif class_name == "java/io/PrintStream" and method_name == "println":
            return JavaClass(json.loads('{"name": "Mock", "methods" :[{"name":"println", "code": { "bytecode": [ { "offset": 0, "opr": "load", "type": "str", "index": 0 }, { "offset": 1, "opr": "print" }, { "offset": 2, "opr": "return", "type": null } ] } } ] }'))
        else:
            return JavaClass(json.loads('{"name": "Mock", "methods" :[{"name":"' + method_name + '", "code": { "bytecode": [ { "offset": 0, "opr": "push", "value": { "type": "integer", "value": 4 } }, { "offset": 1, "opr": "return", "type": "int" } ] } } ] }'))

    def run(self, class_name: str, method_name: str, method_args: List[Value]) -> Value:
        self.stack.append(StackElement(method_args, [], Counter(method_name, 0)))

        while len(self.stack) > 0:
            element = self.stack.pop()
            operation = Operation(self.get_class(class_name, method_name).get_method(element.counter.method_name)["code"]["bytecode"][element.counter.counter], self.bytecode_interpreter.create_value)
            result = self.run_operation(operation, element)
            if operation.get_name() == "return":
                return result
        raise Exception("Raised end without breaking")

    def run_operation(self, operation: Operation, element: StackElement) -> Value | None:
        operation_name = operation.get_name()

        match operation_name:
            case "invoke":
                self.create_stack_frame(operation, element)
            case "return":
                return self.bytecode_interpreter.execute(operation_name, self, operation, element)
            case _:
                self.bytecode_interpreter.execute(operation_name, self, operation, element)

    def create_stack_frame(self, opr, element):
        method_name = opr.method["name"]
        class_name = opr.method["ref"]["name"]
        args = []
        for _ in range(len(opr.method["args"])):
            args.append(element.operational_stack.pop())
        args.reverse()
        self.stack_of_stacks.append([])
        self.stack = self.stack_of_stacks[-1]
        self.stack.append(StackElement(args, [], Counter(method_name, 0)))
        result = self.run(class_name, method_name, args)

        # Note that this currently allows memory mutation
        
        self.stack_of_stacks.pop()
        self.stack = self.stack_of_stacks[-1]
        if opr.method["returns"] is not None:
            self.stack.append(StackElement(element.local_variables, element.operational_stack + [result], element.counter.next_counter()))
        else:
            self.stack.append(StackElement(element.local_variables, element.operational_stack, element.counter.next_counter()))
    
    def run_analysis(self, class_name: str, method_name: str, method_args: List[Value]) -> Value:
        self.stack.append(StackElement(method_args, [], Counter(method_name, 0)))

        k = 100
        for _ in range(k):
            element = self.stack.pop()
            operation = Operation(self.get_class(class_name, method_name).get_method(element.counter.method_name)["code"]["bytecode"][element.counter.counter], self.bytecode_interpreter.create_value)
            result = self.run_analysis_operation(operation, element)
            if len(self.exceptions) > 0:
                return self.exceptions[0]
            if operation.get_name() == "return":
                return result
    
    def run_analysis_operation(self, operation: Operation, element: StackElement) -> Value | None:
        operation_name = operation.get_name()

        if operation_name == "return":
            return self.bytecode_interpreter.execute(operation_name, self, operation, element)
        self.bytecode_interpreter.execute(operation_name, self, operation, element)

def generate_unbounded_params(java_method: JsonDict) -> List[Value]:
    """
    Now, we will be creating parameters to pass the function
    Feel free to change the signature
    """
    raise NotImplementedError()

def run_program_analysis(java_program: JavaProgram):
    # Ignore this for now
    raise NotImplementedError

def run_method_analysis(java_class: JavaClass,
                        method_name: str,
                        stdout:OutputBuffer=OutputBuffer()) -> Tuple[bool, Optional[AnalysisException]]:
    args = []
    memory = {}
    abstraction = RangeAbstraction()
    interpreter = Interpreter(java_program=java_class, 
                              memory=memory,
                              bytecode_interpreter=abstraction,
                              stdout=stdout)
    
    method_args = interpreter.get_class(java_class.name, method_name).get_method(method_name)["params"]
    for arg in method_args:
        if arg["type"]["base"] == "int":
            value = abstraction.create_int_argument()
            args.append(value)

    result = interpreter.run_analysis(java_class.name, method_name, args)
    if type(result) is AnalysisException:
        return (True, result)
    else:
        return (False, None)


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
        if type(arg) is ArrayValue:
            memory_address = uuid.uuid4()
            memory[memory_address] = arg
            args.append(Value(memory_address))
        elif type(arg) is Value:
            args.append(arg)

    interpreter = Interpreter(java_program=java_class, 
                              memory=memory, 
                              stdout=stdout)
    return interpreter.run(java_class.name, method_name, args)
