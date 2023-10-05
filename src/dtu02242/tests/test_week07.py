from dtu02242.week_07.data_structures import *
from dtu02242.week_07.interpreter import run_method, run_method_analysis
from dtu02242.week_07.parser import JavaClass
from typing import List, Any
import json
import pytest

class TestErrors:
    pass


class TestSimple:
    with open("course-02242-examples/decompiled/dtu/compute/exec/Simple.json", "r") as fp:
        json_dict = json.load(fp)
        java_class = JavaClass(json_dict=json_dict)

    def test_noop(self):
        result = run_method(self.java_class, "noop", [], None).get_value()
        assert result is None

    def test_zero(self):
        result = run_method(self.java_class, "zero", [], None).get_value()
        assert result == 0

    def test_hundredAndTwo(self):
        result = run_method(self.java_class, "hundredAndTwo", [], None).get_value()
        assert result == 102

    def test_identity(self):
        assert run_method(self.java_class, "identity", wrap([1]), None).get_value() == 1
        assert run_method(self.java_class, "identity", wrap([2]), None).get_value() == 2
        assert run_method(self.java_class, "identity", wrap([-5]), None).get_value() == -5

    def test_add(self):
        # Sanity check
        assert run_method(self.java_class, "add", wrap([1, 1]), None).get_value() == 2
        assert run_method(self.java_class, "add", wrap([0, 1]), None).get_value() == 1
        assert run_method(self.java_class, "add", wrap([-1, 1]), None).get_value() == 0

    def test_min(self):
        assert run_method(self.java_class, "min", wrap([-1, 1]), None).get_value() == -1
        assert run_method(self.java_class, "min", wrap([1, -1]), None).get_value() == -1
        assert run_method(self.java_class, "min", wrap([1, 1]), None).get_value() == 1

    def test_factorial(self):
        assert run_method(self.java_class, "factorial", wrap([1]), None).get_value() == 1
        assert run_method(self.java_class, "factorial", wrap([2]), None).get_value() == 2
        assert run_method(self.java_class, "factorial", wrap([3]), None).get_value() == 6
        assert run_method(self.java_class, "factorial", wrap([4]), None).get_value() == 24
        assert run_method(self.java_class, "factorial", wrap([5]), None).get_value() == 120
        assert run_method(self.java_class, "factorial", wrap([6]), None).get_value() == 720


class TestArray:
    with open("course-02242-examples/decompiled/dtu/compute/exec/Array.json", "r") as fp:
        json_dict = json.load(fp)
        java_class = JavaClass(json_dict=json_dict)

    def test_first(self):
        array = [0, 1, 3]
        assert run_method(self.java_class, "first", wrap([array]), None).get_value() == 0
        # array_empty = RefValue(ArrayValue([])) # TODO: Java still types empty arrays, so should handle that
        # assert run_method(self.java_class, "first", { "vals" : array }, None).get_value() == 0
        # No way to assert this right now without deciding on error handling
        # Best to use our own classes rather than relying on Python exceptions as Python 
        # exceptions can be inflexible

    def test_firstSafe(self):
        array = [1, 2, 3]
        assert run_method(self.java_class, "firstSafe", wrap([array]), None).get_value() == 1
        with pytest.raises(Exception) as ex:
            run_method(self.java_class, "firstSafe", wrap([[]]), None).get_value()
        assert str(ex.value) == "java/lang/AssertionError" 
        # need to decide on how to handle Java assert statements
        #array = RefValue(ArrayValue([]))
        #assert run_method(self.java_class, "firstSafe", { "vals" : array }, None).get_value() == IntValue(0)


    def test_access(self):        
        array = [0, 1, 3]
        assert run_method(self.java_class, "access", wrap([0, array]), None).get_value() == 0
        assert run_method(self.java_class, "access", wrap([1, array]), None).get_value() == 1
        assert run_method(self.java_class, "access", wrap([2, array]), None).get_value() == 3

    def test_newArray(self):
        assert run_method(self.java_class, "newArray", [], None).get_value() == 1

    def test_newArrayOutOfBounds(self):
        with pytest.raises(Exception) as ex:
            run_method(self.java_class, "newArrayOutOfBounds", [], None).get_value()
        assert str(ex.value) == "Index out of bounds"

    def test_accessSafe(self):
        array = [0, 1, 3]
        assert run_method(self.java_class, "accessSafe", wrap([0, array]), None).get_value() == 0
        assert run_method(self.java_class, "accessSafe", wrap([1, array]), None).get_value() == 1
        assert run_method(self.java_class, "accessSafe", wrap([2, array]), None).get_value() == 3
        with pytest.raises(Exception) as ex_1:
            run_method(self.java_class, "accessSafe", wrap([3, array]), None).get_value()
        assert str(ex_1.value) == "java/lang/AssertionError"
        with pytest.raises(Exception) as ex_2:
            run_method(self.java_class, "accessSafe", wrap([-1, array]), None).get_value()
        assert str(ex_2.value) == "java/lang/AssertionError"

    def test_bubbleSort(self):
        array = wrap([[3, 1, 2]])
        run_method(self.java_class, "bubbleSort", array, None).get_value()
        assert array == wrap([[1, 2, 3]])

    def test_aWierdOneOutOfBounds(self):
        with pytest.raises(Exception) as ex:
            run_method(self.java_class, "aWierdOneOutOfBounds", [], None).get_value()
        assert str(ex.value) == "Index out of bounds"

    def test_aWierdOneWithinBounds(self):
        assert run_method(self.java_class, "aWierdOneWithinBounds", [], None).get_value() == 1

class TestCalls:
    with open("course-02242-examples/decompiled/dtu/compute/exec/Calls.json", "r") as fp:
        json_dict = json.load(fp)
        java_class = JavaClass(json_dict=json_dict)

    def test_helloWorld(self, capsys):
        stdout = OutputBuffer()
        run_method(self.java_class, "helloWorld", [], None, stdout)
        assert stdout.buffer == "Hello, World!\n"

    def test_fib(self):
        assert run_method(self.java_class, "fib", wrap([0])).get_value() == 1
        assert run_method(self.java_class, "fib", wrap([1])).get_value() == 1
        assert run_method(self.java_class, "fib", wrap([2])).get_value() == 2
        assert run_method(self.java_class, "fib", wrap([3])).get_value() == 3
        assert run_method(self.java_class, "fib", wrap([4])).get_value() == 5
        assert run_method(self.java_class, "fib", wrap([5])).get_value() == 8
        assert run_method(self.java_class, "fib", wrap([6])).get_value() == 13
        # after this point, the method should be so slow that it is a waste of time to test


class TestArithmetics:
    """
    Mostly analyzes division by zero
    """
    with open("course-02242-examples/decompiled/eu/bogoe/dtu/exceptional/Arithmetics.json", "r") as fp:
        json_dict = json.load(fp)
        java_class = JavaClass(json_dict=json_dict)

    def test_alwaysThrows1(self):
        # No arguments
        # Always throws ArithmeticException
        result = run_method_analysis(self.java_class, "alwaysThrows1")
        assert result == ArithmeticException

    def test_alwaysThrows2(self):
        # 1 argument
        # Always throws ArithmeticException regardless of argument
        result = run_method_analysis(self.java_class, "alwaysThrows2")
        assert result == ArithmeticException

    def test_alwaysThrows3(self):
        # 2 arguments
        # Throws ArithmeticException if and only if argument 2 is zero
        result = run_method_analysis(self.java_class, "alwaysThrows3")
        assert result == ArithmeticException

    def test_alwaysThrows4(self):
        # 2 arguments
        # throws AssertionError if argument 1 above -1 and argument 2 above 1
        # throws ArithmeticException if argument 2 is zero
        result = run_method_analysis(self.java_class, "alwaysThrows4")
        assert result == ArithmeticException

    def test_alwaysThrows5(self):
        # 2 arguments
        # throws AssertionError if argument 1 above -1 and argument 2 above 1
        # throws ArithmeticException if argument 2 is zero
        result = run_method_analysis(self.java_class, "alwaysThrows5")
        assert result == ArithmeticException

    def test_itDependsOnLattice1(self):
        # No arguments
        # doesn't throw, always returns 1
        result = run_method_analysis(self.java_class, "itDependsOnLattice1")
        assert result == MaybeCorrect

    def test_itDependsOnLattice2(self):
        # No arguments
        # doesn't throw, always returns -1
        result = run_method_analysis(self.java_class, "itDependsOnLattice2")
        assert result == MaybeCorrect

    def test_itDependsOnLattice3(self):
        # 2 arguments
        # throws AssertionError if arg1 <= 1000 or arg2 <= 10
        # specifically throws ArithmeticException if arg1 is 10 times arg2 (difficult to catch)
        result = run_method_analysis(self.java_class, "itDependsOnLattice3")
        # Our abstraction is not expected to catch this issue
        assert result == MaybeCorrect

    def test_itDependsOnLattice4(self):
        # No arguments
        # Always throws ArithmeticException
        pass

    def test_neverThrows1(self):
        # No arguments
        # Never throws, returns 0
        pass

    def test_neverThrows2(self):
        # 1 argument
        # throws AssertionError if arg1 <= 0
        # Never throws, returns 0
        pass

    def test_neverThrows3(self):
        # 2 argument
        # throws AssertionError if arg1 <= 0
        # throws AssertionError if arg2 != 0
        # Never throws, returns 0
        pass

    def test_neverThrows4(self):
        # 2 argument
        # throws AssertionError if arg1 <= 0
        # throws AssertionError if arg2 >= 0
        # Never throws, returns 0
        pass

    def test_neverThrows5(self):
        # 2 argument
        # Never throws, returns same sign as arg2
        pass

    def test_speedVsPrecision(self):
        # No args
        # throws ArithmeticException but takes a while to get there
        pass