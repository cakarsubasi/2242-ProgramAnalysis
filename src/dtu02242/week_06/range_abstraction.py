from typing import Any
from .bytecode import ByteCode, IInterp, Operation, StackElement
from .data_structures import Value, AnalysisExceptionTypes, AnalysisException

INT_MINIMUM = -2147483648
INT_MAXIMUM = 2147483647

class Range:
    from_: int
    to: int

    def __init__(self, from_: int, to: int):
        self.from_ = from_
        self.to = to

class RangeValue(Value):
    type_name = "range_list"

    def __init__(self, value: Any, type_name: str = "void"):
        if type(value) is RangeValue:
            raise Exception("Values shouldn't be nested!")
        if type(value) in [int, float]:
            self._value = [Range(value, value)]
            self.type_name = self.type_name
        elif self.type_name == self.type_name:
            self._value = value
            self.type_name = self.type_name
        else:
            super.__init__(value, type_name)
    
    def __truediv__(self, other: 'RangeValue'):
        for range in other._value:
            if range.from_ <= 0 and range.to >= 0:
                return AnalysisException(AnalysisExceptionTypes.ArithmeticException)
            if range.from_ == 0:
                return AnalysisException(AnalysisExceptionTypes.ArithmeticException)
            if range.to == 0:
                return AnalysisException(AnalysisExceptionTypes.ArithmeticException)
        
        result = []
        for left_range in self._value:
            for right_range in other._value:
                result.append(Range(left_range.from_ / right_range.to, left_range.to / right_range.from_))

        return RangeValue(result, self.type_name)
    
    def __sub__(self, other: 'Value'):
        result = []
        for left_range in self._value:
            for right_range in other._value:
                result.append(Range(left_range.from_ - right_range.to, left_range.to - right_range.from_))

        return RangeValue(result, self.type_name)


class RangeAbstraction(ByteCode):

    def __init__(self):
        super().__init__()
    
    def create_value(self, value: Any, type_name: str = "void") -> Value:
        return RangeValue(value, type_name)
    
    def create_int_argument(self):
        return RangeValue([Range(INT_MINIMUM, INT_MAXIMUM)], RangeValue.type_name)
    
    def create_float_argument(self):
        # NOTE: Floats are weird so this is just the same as ints
        return RangeValue([Range(INT_MINIMUM, INT_MAXIMUM)], RangeValue.type_name)
    
    def perform_div(self, runner: IInterp, opr: Operation, element: StackElement):
        second = element.operational_stack.pop()
        first = element.operational_stack.pop()
        result = first / second
        if type(result) is AnalysisException:
            runner.exceptions.append(result)
        runner.stack.append(StackElement(element.local_variables, element.operational_stack + [result], element.counter.next_counter()))