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
                self.null = True
                self.identifier = None

class AbstractArray:
    def __init__(self, abstract_len : AbstractValue) :
        self.length = abstract_len
        self.values = []
    
    length : AbstractValue
    values : List[AbstractValue]

class AbstractState:
    def __init__ (self, stack : List[AbstractValue], args : List[AbstractValue]) :
        self.stack = stack
        self.args = args
        self.pc = 0
        self.arrays = {}

    stack : List[AbstractValue]
    args : List[AbstractValue]
    pc : int


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

            if (abstract_index.max != abstract_index.min or len(new_state.arrays) == 0) :
                print("Here might be out of range exception: ", byte_code[pc], pc, method_name)
            if (abstract_reference.null):
                print("Here might be null pointer: ", byte_code[pc], pc, method_name)

        elif opr["opr"] == "get":
            if opr["field"]["name"] == "$assertionsDisabled" :
                print("Found assertion")
        
        elif opr["opr"] == "newarray" :
            abstract_len = new_state.stack.pop()
            indentifier = "$" + str(len(new_state.arrays))
            new_state.arrays[indentifier] = AbstractArray(abstract_len)
            
            new_reference = AbstractValue("reference")
            new_reference.identifier = indentifier

            new_state.args.append(new_reference)

            # Add inner interpretation of new array

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
    bounded_abstract_interpretation(java_class.get_method("first")["code"]["bytecode"], [array], 10, "first")
    bounded_abstract_interpretation(java_class.get_method("newArray")["code"]["bytecode"], [array], 10, "newArray")