import json
import uuid
from typing import List, Dict, Any, Iterable, Optional, Type
from dataclasses import dataclass

JsonDict = Dict[str, Any]

class JavaClass:
    def __init__(self, json_dict: JsonDict) -> None:
        self.name = json_dict['name']
        self.json_dict = json_dict

    def get_methods(self) -> List[JsonDict]:
        methods: List[JsonDict] = self.json_dict["methods"]
        return methods
    
    def get_method(self, name: str) -> Optional[JsonDict]:
        methods = self.get_methods()
        for method in methods:
            if method["name"] == name:
                return method
        return None
    
    def __str__(self) -> str:
        return self.json_dict["name"]

# def run_method(java_class: JavaClass, method_name: str, method_args: List[JavaValue], environment: Optional[JavaProgram]=None) -> JavaValue | JavaError:
#     # This is the entry point, this function should create an
#     # Interpreter instance, and then run it with the given
#     # properties. It should raise an error
#     # if it gets unexpected or inadequate arguments

#     # The environment should allow referencing other classes

#     args = []
#     memory = {}
#     for arg in method_args:
#         type_name = type(arg).__name__
#         if type_name == "list":
#             memory_address = uuid.uuid4()
#             memory[memory_address] = ArrayValue(len(arg), arg)
#             args.append(Value(memory_address))
#         else:
#             args.append(Value(arg, type_name))

#     interpreter = Interpreter(java_class, method_name, args, memory)
#     return interpreter.run()

class Value:
    def __init__(self, value: Any, type_name: str = None):
        self.value = value
        if type_name is None:
            self.type_name = type(value).__name__ 
        else:
            self.type_name = type_name

class AbstractValue:
    def __init__(self, type):
            self.type = type
            if type == "integer":
                self.max = 2147483647
                self.min = -2147483646
            if type == "reference":
                self.min = 0
                self.max = 4294967295

class AbstractState:
    def __init__ (self, stack : List[AbstractValue], args : List[AbstractValue]) :
        self.stack = stack
        self.args = args
        self.pc = 0
        self.error = False
        self.valid_length = False
        self.err_type = None

    stack : List[AbstractValue]
    args : List[AbstractValue]
    pc : int
    error : bool
    err_type : str
    valid_length : bool


class Abstraction:
    def __init__ (self, byte_code : JsonDict, method_args: List[Value]):
        self.method_args = method_args
        self.byte_code = byte_code

    def toAbstractArgs(self) -> List[AbstractValue] :
        abstract_args = []

        for arg in self.method_args:
            if type(arg).__name__ == "int" :
                abstract_int = AbstractValue("integer")
                abstract_args.append(abstract_int)
            if type(arg).__name__ == "list" :
                abstract_reference = AbstractValue("reference")
                abstract_args.append(abstract_reference)

        return abstract_args
    
    def abstract_step(self, byte_code : JsonDict, state : AbstractState, pc : int, method_name : str) -> (AbstractState, int) :
        new_state = state
        
        if pc > len(byte_code)-1 :
            return (None, 0)
        opr = byte_code[pc]
        
        if opr["opr"] == "load" :
            new_state.stack.append(state.args.pop(opr["index"]))
        elif opr["opr"] == "push":
            if opr["value"]["type"] == "integer":
                abstract_value = AbstractValue("integer")
                abstract_value.min = opr["value"]["value"]
                abstract_value.max = abstract_value.min
                new_state.stack.append(abstract_value)
        elif opr["opr"] == "array_load":
            abstract_index = new_state.stack.pop()
            abstract_reference = new_state.stack.pop()

            if (abstract_index.max != abstract_index.min or not(new_state.valid_length)) :
                print("Here might be out of range exception: ", byte_code[pc], pc, method_name)
            if (abstract_reference.max != abstract_reference.min):
                print("Here might be null pointer: ", byte_code[pc], pc, method_name)
        
        return (new_state, pc+1)

def bounded_abstract_interpretation( byte_code : JsonDict, method_args: List[Value], max_iter : int, method_name : str) :
    abstract = Abstraction(byte_code, method_args)
    abstrac_args = abstract.toAbstractArgs()
    
    initial_state = AbstractState([], abstrac_args)
    state_copy = initial_state

    for k in range(0, max_iter):
        (ns, npc) = abstract.abstract_step(byte_code, state_copy, initial_state.pc, method_name)
        if (ns == None) :
            break
        initial_state.pc = npc


with open("Array.json", "r") as fp:
    json_dict = json.load(fp)
    java_class = JavaClass(json_dict=json_dict)

    array = [1,2,3]

    bounded_abstract_interpretation(java_class.get_method("access")["code"]["bytecode"], [1, array], 10, "access")
    bounded_abstract_interpretation(java_class.get_method("first")["code"]["bytecode"], array, 10, "first")