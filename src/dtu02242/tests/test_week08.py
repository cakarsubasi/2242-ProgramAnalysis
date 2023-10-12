from dtu02242.week_07.data_structures import *
from dtu02242.week_07.interpreter import run_method, run_method_analysis
from dtu02242.week_07.parser import JavaClass
from typing import List, Any
import json
import pytest

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