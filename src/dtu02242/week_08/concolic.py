import z3
import random
from typing import Dict, Any, List
# from dtu02242.week_08.parser import JsonDict, JavaClass
from dataclasses import dataclass
from enum import Enum

if __name__ == "__main__":
    from parser import JsonDict, JavaClass
else:
    from dtu02242.week_08.parser import JsonDict, JavaClass

class AnalysisResultValue(Enum):
    No = 0
    Maybe = 1
    AssertionError = 2
    IndexOutOfBoundsExecption = 3
    ArithmeticException = 4
    NullPointerException = 5
    UnsupportedOperationException = 6

@dataclass(frozen=True)
class AnalysisResult:
    exception: AnalysisResultValue
    input: z3.ExprRef


@dataclass(frozen=True)
class ConcolicValue:
    concrete: int | bool
    symbolic: z3.ExprRef

    def __repr__(self) -> str:
        return f"{self.concrete} ({self.symbolic})"

    @classmethod
    def from_const(cls, _value: int | bool) -> "ConcolicValue":
        """
        Create a ConcolicValue from a constant
        @return: ConcolicValue
        """
        if isinstance(_value, bool):
            return ConcolicValue(_value, z3.BoolVal(_value))
        if isinstance(_value, int):
            return ConcolicValue(_value, z3.IntVal(_value))
        raise Exception(f"unknown const: {_value}")

    def compare(self, other: "ConcolicValue", op_name: str) -> "ConcolicValue":
        """
        Handle comparison operations (eq, ne, gt, ge, le, lt) etc.
        @return: ConcolicValue result
        """
        # Creating an entire dictionary to check 4 values is cringe
        if op_name == "ne":
            opr = "__ne__"  # name must match Python op names
        elif op_name == "eq":
            opr = "__eq__"
        elif op_name == "gt":
            opr = "__gt__"
        elif op_name == "ge":
            opr = "__ge__"
        elif op_name == "le":
            opr = "__le__"
        elif op_name == "lt":
            opr = "__lt__"
        else:
            raise NotImplementedError(f"Unknown operation: {op_name}")

        return ConcolicValue(
            getattr(self.concrete, opr)(other.concrete),
            z3.simplify(getattr(self.symbolic, opr)(other.symbolic)),
        )

    def binary(self, other: "ConcolicValue", op_name: str) -> "ConcolicValue":
        """
        Handle binary operations (add, sub, mul, div) etc.
        @return: ConcolicValue result
        """
        if op_name == "sub":
            opr = "__sub__"
        elif op_name == "add":
            opr = "__add__"
        elif op_name == "mul":
            opr = "__mul__"
        elif op_name == "div":
            opr = "__div__"
            return ConcolicValue(
                self.concrete // other.concrete,
                # Is this correct?
                z3.simplify(self.symbolic / other.symbolic),
            )
        else:
            raise NotImplementedError(f"Unknown operation: {op_name}")

        return ConcolicValue(
            getattr(self.concrete, opr)(other.concrete),
            z3.simplify(getattr(self.symbolic, opr)(other.symbolic)),
        )

@dataclass(frozen=True)
class ConcolicList:
    elements: List[ConcolicValue]
    length: ConcolicValue

    @classmethod
    def from_conconic(cls, _length: "ConcolicValue", _type: str) -> "ConcolicValue":
        """
        Create a ConcolicValue from a list
        @return: ConcolicValue
        """
        if isinstance(_length.concrete, int):
            if _type == "int":
                return ConcolicList(
                    [ConcolicValue.from_const(0) for _ in range(_length.concrete)],
                    _length
                )
            elif _type == "bool":
                return ConcolicList(
                    [ConcolicValue.from_const(False) for _ in range(_length.concrete)],
                    _length
                )
            else:
                raise Exception(f"Unknown type for array: {_type}")
        raise Exception(f"_length is not an int: {_length}")

    def __getitem__(self, index: ConcolicValue):
        return self.elements[index.concrete]

    def __setitem__(self, index: ConcolicValue, value: ConcolicValue):
        self.elements[index.concrete] = value

@dataclass(frozen=True)
class State:
    locals: Dict[int, ConcolicValue]
    stack: list[ConcolicValue]

    def push(self, _value: ConcolicValue) -> None:
        """
        Push a value into the stack
        """
        if not isinstance(_value, ConcolicValue):
            raise Exception(f"{_value} is not a ConcolicValue")
        self.stack.append(_value)

    def pop(self) -> ConcolicValue:
        """
        Pop a value from the stack and return it
        """
        return self.stack.pop()

    def load(self, index: int) -> None:
        """
        Load the local in the given index to the stack
        """
        self.push(self.locals[index])

    def store(self, index: int) -> None:
        """
        Pop the stack to the given local index
        """
        self.locals[index] = self.pop()


@dataclass(frozen=True)
class Bytecode:
    dictionary: JsonDict

    def __getattr__(self, __name: str) -> Any:
        return self.dictionary[__name]

    def __repr__(self) -> str:
        return (
            f"bc:{self.opr}"
            + " { "
            + ", ".join(
                f"{k}: {v}"
                for k, v in self.dictionary.items()
                if k != "opr" and k != "offset"
            )
            + " }"
        )


def concolic(program: JavaClass, method_name: str, max_depth=1000, debug_print=False):
    random.seed(1)
    method = program.get_method(method_name)
    memory: Dict[int, ConcolicList] = {}

    solver = z3.Solver()

    # TODO: Cover things other than ints
    params = []
    for i, param in enumerate(method["params"]):
        _type = param["type"]
        if "base" in _type and _type["base"] in ["int", "float"]:
            params.append(z3.Int(f"p{i}"))
        elif "kind" in _type and _type["kind"] == "array" and _type["type"]["base"] in ["int", "float"]:
            params.append(z3.Int(f"a_i{i}"))
        elif "kind" in _type and _type["kind"] == "array" and _type["type"]["base"] == "bool":
            params.append(z3.Bool(f"a_b{i}"))
        else:
            raise Exception(f"Unknown parameter type: {_type}")
    bytecode = [Bytecode(b) for b in method["code"]["bytecode"]]

    terminations: List[AnalysisResultValue, z3.ExprRef] = []

    # With no assumptions, z3 will return sat
    while solver.check() == z3.sat:
        model = solver.model()

        # Create input state
        inputs = [model.eval(p, model_completion=True).as_long() for p in params]
        state = State({}, [])
        for idx, (conc, symb) in enumerate(zip(inputs, params)):
            a = str(symb)
            if str(symb).startswith("p"):
                state.locals[idx] = ConcolicValue(conc, symb)
            elif str(symb).startswith("a_i"):
                memory_address = random.randint(0, 2**128)
                array = ConcolicList.from_conconic(ConcolicValue(conc, symb), "int")
                memory[memory_address] = array
                state.locals[idx] = ConcolicValue.from_const(memory_address)
            elif str(symb).startswith("a_b"):
                memory_address = random.randint(0, 2**128)
                array = ConcolicList.from_conconic(ConcolicValue(conc, symb), "bool")
                memory[memory_address] = array
                state.locals[idx] = ConcolicValue.from_const(memory_address)

        pc = 0
        path = []

        for _ in range(max_depth):
            bc = bytecode[pc]
            pc += 1

            if debug_print:
                print("-------")
                print(f"pc: {pc}")
                print(state)
                print(path)
                print(bc)

            if bc.opr == "get":
                if bc.field["name"] == "$assertionsDisabled":
                    state.push(ConcolicValue.from_const(False))
                elif bc.field["type"]["name"] == "java/io/PrintStream":
                    continue

            # branching operations
            elif bc.opr == "ifz":
                value = state.pop()
                # Create zero variable for comparison
                zero = ConcolicValue.from_const(0)
                value_r = value.compare(zero, bc.condition)
                # Not sure about the logic behind this jump
                if value_r.concrete:
                    pc = bc.target
                    path.append(value_r.symbolic)
                else:
                    path.append(z3.simplify(z3.Not(value_r.symbolic)))
            elif bc.opr == "if":
                value2 = state.pop()
                value1 = state.pop()
                value_r = value1.compare(value2, bc.condition)
                # Not sure about the logic behind this jump
                if value_r.concrete:
                    pc = bc.target
                    path.append(value_r.symbolic)
                else:
                    path.append(z3.simplify(z3.Not(value_r.symbolic)))
            elif bc.opr == "goto":
                pc = bc.target

            # arithmetic operations
            elif bc.opr == "binary":
                value2 = state.pop()
                value1 = state.pop()
                if bc.operant == "div" and value2.concrete == 0:
                    result = AnalysisResultValue.ArithmeticException
                    path.append(value2.symbolic == 0)
                    break
                else:
                    path.append(z3.simplify(z3.Not(value2.symbolic == 0)))
                value_r = value1.binary(value2, bc.operant)
                state.push(value_r)
            elif bc.opr == "incr":
                state.load(bc.index)
                value = state.pop()
                state.push(value.binary(ConcolicValue.from_const(bc.amount), "add"))
                state.store(bc.index)
            elif bc.opr == "negate":
                value = state.pop()
                state.push(value.binary(ConcolicValue.from_const(-1), "mul"))
            # array operations
            elif bc.opr == "newarray":
                size = state.pop()
                memory_address = random.randint(0, 2**128)
                array = ConcolicList.from_conconic(size, bc.type)
                memory[memory_address] = array
                state.push(ConcolicValue.from_const(memory_address))
            elif bc.opr == "array_store":
                value_to_store = state.pop()
                index = state.pop()
                arr_address = state.pop()
                arr = memory[arr_address.concrete]
                if index.concrete < 0:
                    result = AnalysisResultValue.IndexOutOfBoundsExecption
                    path.append(index.symbolic < 0)
                    break
                if index.concrete >= arr.length.concrete:
                    result = AnalysisResultValue.IndexOutOfBoundsExecption
                    path.append(index.symbolic >= arr.length.symbolic)
                    break
                path.append(z3.simplify(z3.Not(index.symbolic < 0)))
                path.append(z3.simplify(z3.Not(index.symbolic >= arr.length.symbolic)))
                memory[arr_address.concrete][index] = value_to_store
            elif bc.opr == "array_load":
                index = state.pop()
                arr_address = state.pop()
                arr = memory[arr_address.concrete]
                if index.concrete < 0:
                    result = AnalysisResultValue.IndexOutOfBoundsExecption
                    path.append(index.symbolic < 0)
                    break
                if index.concrete >= arr.length.concrete:
                    result = AnalysisResultValue.IndexOutOfBoundsExecption
                    path.append(index.symbolic >= arr.length.symbolic)
                    break
                value = arr[index]
                path.append(z3.simplify(z3.Not(index.symbolic < 0)))
                path.append(z3.simplify(z3.Not(index.symbolic >= arr.length.symbolic)))
                state.push(value)
            elif bc.opr == "arraylength":
                arr_address = state.pop()
                arr_length = memory[arr_address.concrete].length
                state.push(arr_length)
            # misc
            elif (
                bc.opr == "new" and bc.dictionary["class"] == "java/lang/AssertionError"
            ):
                result = AnalysisResultValue.AssertionError
                break
            elif bc.opr == "dup":
                value = state.pop()
                state.push(value)
                state.push(value)
            elif bc.opr == "return":
                if bc.type is None:
                    result = AnalysisResultValue.No
                else:
                    value = state.pop()
                    result = AnalysisResultValue.No
                break
            elif bc.opr == "invoke":
                # We do nothing for now
                pass

            # stack and local operations
            elif bc.opr == "load":
                state.load(bc.index)
            elif bc.opr == "store":
                state.store(bc.index)
            elif bc.opr == "push":
                state.push(ConcolicValue.from_const(bc.value["value"]))
            else:
                raise NotImplementedError(f"Unsupported bytecode: {bc}")
        else:  # The incredibly rare for-else statement!
            result = AnalysisResultValue.Maybe

        path_constraint = z3.simplify(z3.And(*path))
        terminations.append((result, path_constraint))
        print(f"{inputs} -> {result} | {path_constraint}")

        solver.add(z3.Not(path_constraint))
    
    for result, path_constraint in terminations:
        if result not in [AnalysisResultValue.No, AnalysisResultValue.AssertionError]:
            arg_solver = z3.Solver()
            arg_solver.add(path_constraint)
            arg_solver.check()
            arg_model = arg_solver.model()
            args = [arg_model.eval(p, model_completion=True).as_long() for p in params]
            return AnalysisResult(result, args)
    else:
        return AnalysisResult(AnalysisResultValue.No, [])


if __name__ == "__main__":
    import json

    with open(
        "course-02242-examples/decompiled/eu/bogoe/dtu/exceptional/Arithmetics.json",
        "r",
    ) as fp:
        json_dict = json.load(fp)
        program = JavaClass(json_dict)
    result = concolic(program, "alwaysThrows5")
    print(result)
