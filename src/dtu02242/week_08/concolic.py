import z3
from typing import Dict, Any, List
from dtu02242.week_08.parser import JsonDict, JavaClass
from dataclasses import dataclass


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
        elif op_name == "gt":
            opr = "__gt__"
        elif op_name == "ge":
            opr = "__ge__"
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


def concolic(method: JsonDict, max_depth=1000, debug_print=False):
    solver = z3.Solver()

    # TODO: Cover things other than ints
    params = [z3.Int(f"p{i}") for i, _ in enumerate(method["params"])]
    bytecode = [Bytecode(b) for b in method["code"]["bytecode"]]

    # With no assumptions, z3 will return sat
    while solver.check() == z3.sat:
        model = solver.model()

        # Create input state
        inputs = [model.eval(p, model_completion=True).as_long() for p in params]
        state = State(
            {
                idx: ConcolicValue(conc, symb)
                for idx, (conc, symb) in enumerate(zip(inputs, params))
            },
            [],
        )
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

            if bc.opr == "get" and bc.field["name"] == "$assertionsDisabled":
                state.push(ConcolicValue.from_const(False))

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
                    result = "Divide by 0"
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
            # misc
            elif (
                bc.opr == "new" and bc.dictionary["class"] == "java/lang/AssertionError"
            ):
                result = "AssertionError"
                break
            elif bc.opr == "return":
                if bc.type is None:
                    result = f"Return: void"
                else:
                    value = state.pop()
                    result = f"Return: {value}"
                break

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
            result = "Out of Iterations"

        path_constraint = z3.simplify(z3.And(*path))
        print(f"{inputs} -> {result} | {path_constraint}")

        solver.add(z3.Not(path_constraint))


if __name__ == "__main__":
    import json

    with open(
        "course-02242-examples/decompiled/eu/bogoe/dtu/exceptional/Arithmetics.json",
        "r",
    ) as fp:
        json_dict = json.load(fp)
        program = JavaClass(json_dict)
    concolic(program.get_method("itDependsOnLattice3"))
    pass
