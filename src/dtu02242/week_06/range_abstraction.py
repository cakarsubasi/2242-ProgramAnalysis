from typing import Any
from .bytecode import ByteCode, Counter, IInterp, Operation, StackElement
from .data_structures import Value, AnalysisExceptionTypes, AnalysisException

INT_MINIMUM = -2147483648
INT_MAXIMUM = 2147483647
RANGE_TYPE_NAME = "range"

class Range:
    from_: int
    to: int

    def __init__(self, a: int, b: int):
        self.from_ = min(a, b)
        self.to = max(a, b)

class RangeValue(Value):
    def __init__(self, value: Any, type_name: str = "void"):
        if type(value) is RangeValue:
            raise Exception("Values shouldn't be nested!")
        if type(value) in [int, float]:
            self._value = Range(value, value)
            self.type_name = RANGE_TYPE_NAME
        elif type_name == RANGE_TYPE_NAME:
            self._value = value
            self.type_name = RANGE_TYPE_NAME
        else:
            super().__init__(value, type_name)
    
    def __truediv__(self, other: 'RangeValue'):
        if other._value.from_ <= 0 and other._value.to >= 0:
            return AnalysisException(AnalysisExceptionTypes.ArithmeticException)
        if other._value.from_ == 0:
            return AnalysisException(AnalysisExceptionTypes.ArithmeticException)
        if other._value.to == 0:
            return AnalysisException(AnalysisExceptionTypes.ArithmeticException)

        result = Range(self._value.from_ / other._value.to, self._value.to / self._value.from_)

        return RangeValue(result, RANGE_TYPE_NAME)
    
    def __sub__(self, other: 'RangeValue'):
        result_from = self._value.from_ - other._value.to
        result_to = self._value.to - other._value.from_
        result = Range(result_from, result_to)

        if result_from < INT_MINIMUM and result_to < INT_MINIMUM:
            underflow_from = INT_MAXIMUM - (result_from - INT_MINIMUM - 1)
            underflow_to = INT_MAXIMUM - (result_to - INT_MINIMUM - 1)
            result = Range(underflow_from, underflow_to)
        elif result_from < INT_MINIMUM:
            underflow = INT_MAXIMUM - (result_from - INT_MINIMUM - 1)
            result = Range(underflow, result_to)
        elif result_to < INT_MINIMUM:
            underflow = INT_MAXIMUM - (result_to - INT_MINIMUM - 1)
            result = Range(result_from, underflow)

        return RangeValue(result, RANGE_TYPE_NAME)

class RangeAbstraction(ByteCode):

    def __init__(self):
        super().__init__()
    
    def create_value(self, value: Any, type_name: str = "void") -> Value:
        return RangeValue(value, type_name)
    
    def create_int_argument(self):
        return RangeValue(Range(INT_MINIMUM, INT_MAXIMUM), RANGE_TYPE_NAME)
    
    def create_float_argument(self):
        # NOTE: Floats are weird so this is just the same as ints
        return RangeValue(Range(INT_MINIMUM, INT_MAXIMUM), RANGE_TYPE_NAME)
    
    def perform_div(self, runner: IInterp, opr: Operation, element: StackElement):
        second = element.operational_stack.pop()
        first = element.operational_stack.pop()
        result = first / second
        if type(result) is AnalysisException:
            runner.exceptions.append(result)
        runner.stack.append(StackElement(element.local_variables, element.operational_stack + [result], element.counter.next_counter()))