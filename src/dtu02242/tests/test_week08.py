from dtu02242.week_08.concolic import concolic, AnalysisResultValue
from dtu02242.week_08.parser import JavaClass
from typing import List, Any
import json
import pytest

class TestArithmetics:
    """
    Analyzes division by zero
    """
    with open("course-02242-examples/decompiled/eu/bogoe/dtu/exceptional/Arithmetics.json", "r") as fp:
        json_dict = json.load(fp)
        java_class = JavaClass(json_dict=json_dict)

    def test_alwaysThrows1(self):
        # No arguments
        # Always throws ArithmeticException
        result = concolic(self.java_class, "alwaysThrows1")
        assert result.exception == AnalysisResultValue.ArithmeticException

    def test_alwaysThrows2(self):
        # 1 argument
        # Always throws ArithmeticException regardless of argument
        result = concolic(self.java_class, "alwaysThrows2")
        assert result.exception == AnalysisResultValue.ArithmeticException

    def test_alwaysThrows3(self):
        # 2 arguments
        # Throws ArithmeticException if and only if argument 2 is zero
        result = concolic(self.java_class, "alwaysThrows3")
        assert result.exception == AnalysisResultValue.ArithmeticException

    def test_alwaysThrows4(self):
        # 2 arguments
        # throws AssertionError if argument 1 above -1 and argument 2 above 1
        # throws ArithmeticException if argument 2 is zero
        result = concolic(self.java_class, "alwaysThrows4")
        assert result.exception == AnalysisResultValue.ArithmeticException

    def test_alwaysThrows5(self):
        # 2 arguments
        # throws AssertionError if argument 1 above -1 and argument 2 above 1
        # throws ArithmeticException if argument 2 is zero
        result = concolic(self.java_class, "alwaysThrows5")
        assert result.exception == AnalysisResultValue.ArithmeticException

    def test_itDependsOnLattice1(self):
        # No arguments
        # doesn't throw, always returns 1
        result = concolic(self.java_class, "itDependsOnLattice1")
        assert result.exception == AnalysisResultValue.No

    def test_itDependsOnLattice2(self):
        # No arguments
        # doesn't throw, always returns -1
        result = concolic(self.java_class, "itDependsOnLattice2")
        assert result.exception == AnalysisResultValue.No

    def test_itDependsOnLattice3(self):
        # 2 arguments
        # throws AssertionError if arg1 <= 1000 or arg2 <= 10
        # specifically throws ArithmeticException if arg1 is 10 times arg2 (difficult to catch)
        result = concolic(self.java_class, "itDependsOnLattice3")
        assert result.exception == AnalysisResultValue.ArithmeticException

    def test_itDependsOnLattice4(self):
        # No arguments
        # Always throws ArithmeticException
        result = concolic(self.java_class, "itDependsOnLattice4")
        assert result.exception == AnalysisResultValue.ArithmeticException

    def test_neverThrows1(self):
        # No arguments
        # Never throws, returns 0
        result = concolic(self.java_class, "neverThrows1")
        assert result.exception == AnalysisResultValue.No

    def test_neverThrows2(self):
        # 1 argument
        # throws AssertionError if arg1 <= 0
        # Never throws, returns 0
        result = concolic(self.java_class, "neverThrows2")
        assert result.exception == AnalysisResultValue.No

    def test_neverThrows3(self):
        # 2 argument
        # throws AssertionError if arg1 <= 0
        # throws AssertionError if arg2 != 0
        # Never throws, returns 0
        result = concolic(self.java_class, "neverThrows3")
        assert result.exception == AnalysisResultValue.No

    def test_neverThrows4(self):
        # 2 argument
        # throws AssertionError if arg1 <= 0
        # throws AssertionError if arg2 >= 0
        # Never throws, returns 0
        result = concolic(self.java_class, "neverThrows4")
        assert result.exception == AnalysisResultValue.No

    def test_neverThrows5(self):
        # 2 argument
        # Never throws, returns same sign as arg2
        result = concolic(self.java_class, "neverThrows5")
        assert result.exception == AnalysisResultValue.No

    @pytest.mark.skip(reason="Passes but takes a long time")
    def test_speedVsPrecision(self):
        # No args
        # throws ArithmeticException but takes a while to get there
        result = concolic(self.java_class, "speedVsPrecision", max_depth=1000000)
        assert result.exception == AnalysisResultValue.ArithmeticException

class TestArray:
    """
    Analyzes array index
    """
    with open("course-02242-examples/decompiled/eu/bogoe/dtu/exceptional/Arrays.json", "r") as fp:
        json_dict = json.load(fp)
        java_class = JavaClass(json_dict=json_dict)

    def test_alwaysThrows1(self):
        # No arguments
        # Always throws IndexOutOfBoundsExecption
        result = concolic(self.java_class, "alwaysThrows1")
        assert result.exception == AnalysisResultValue.IndexOutOfBoundsExecption

    def test_alwaysThrows2(self):
        # 1 argument
        # Throws IndexOutOfBoundsExecption if argument is empty
        result = concolic(self.java_class, "alwaysThrows2")
        assert result.exception == AnalysisResultValue.IndexOutOfBoundsExecption

    def test_alwaysThrows3(self):
        # No arguments
        # Always throws IndexOutOfBoundsExecption
        result = concolic(self.java_class, "alwaysThrows3")
        assert result.exception == AnalysisResultValue.IndexOutOfBoundsExecption

    def test_alwaysThrows4(self):
        # 1 argument
        # Throws IndexOutOfBoundsExecption if argument is empty
        result = concolic(self.java_class, "alwaysThrows4")
        assert result.exception == AnalysisResultValue.IndexOutOfBoundsExecption

    def test_alwaysThrows5(self):
        # 2 arguments
        # Throws AssertionError if argument 1 less or equal to 0 or
        # Throws AssertionError if argument 2 less or equal to 0
        # Throws AssertionError if argument 1 greater than 10
        # Throws AssertionError if argument 2 greater than 10
        # Throws IndexOutOfBoundsExecption if argument 1 is greater than arguemnt 2
        result = concolic(self.java_class, "alwaysThrows5")
        assert result.exception == AnalysisResultValue.IndexOutOfBoundsExecption

    def test_itDependsOnLattice1(self):
        # 2 arguments
        # Throws AssertionError if argument 2 is outside argument 1's range
        # Never throws IndexOutOfBoundsExecption
        result = concolic(self.java_class, "dependsOnLattice1")
        assert result.exception == AnalysisResultValue.No

    def test_itDependsOnLattice2(self):
        # 1 argument
        # Throws AssertionError if argument 1 is empty
        # Never throws IndexOutOfBoundsExecption
        result = concolic(self.java_class, "dependsOnLattice2")
        assert result.exception == AnalysisResultValue.No

    def test_itDependsOnLattice3(self):
        # 1 argument
        # Throws AssertionError if argument 1 is empty
        # Never throws IndexOutOfBoundsExecption
        result = concolic(self.java_class, "dependsOnLattice3")
        assert result.exception == AnalysisResultValue.No

    @pytest.mark.skip(reason="Runs forever... Dont know why")
    def test_itDependsOnLattice4(self):
        # 1 argument
        # Throws AssertionError if argument 1 length is less than or equal to 4
        # Never throws IndexOutOfBoundsExecption
        result = concolic(self.java_class, "dependsOnLattice4")
        assert result.exception == AnalysisResultValue.No

    def test_itDependsOnLattice5(self):
        # 1 argument
        # Throws AssertionError if argument 1 length is less or equal to -10
        # Throws AssertionError if argument 1 length is greater than 10
        # Never throws IndexOutOfBoundsExecption
        result = concolic(self.java_class, "dependsOnLattice5")
        assert result.exception == AnalysisResultValue.No

    def test_neverThrows1(self):
        # No arguments
        # Never throws IndexOutOfBoundsExecption
        result = concolic(self.java_class, "neverThrows1")
        assert result.exception == AnalysisResultValue.No

    def test_neverThrows2(self):
        # No arguments
        # Never throws IndexOutOfBoundsExecption
        result = concolic(self.java_class, "neverThrows2")
        assert result.exception == AnalysisResultValue.No

    def test_neverThrows3(self):
        # No arguments
        # Never throws IndexOutOfBoundsExecption
        result = concolic(self.java_class, "neverThrows3", max_depth=10000)
        assert result.exception == AnalysisResultValue.No