from dtu02242.week_07_oliver.analyzer import run_method_analysis, AnalysisResult
from dtu02242.week_07_oliver.parser import JavaClass
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
        assert AnalysisResult.ArithmeticException in result

    def test_alwaysThrows2(self):
        # 1 argument
        # Always throws ArithmeticException regardless of argument
        result = run_method_analysis(self.java_class, "alwaysThrows2")
        assert AnalysisResult.ArithmeticException in result

    def test_alwaysThrows3(self):
        # 2 arguments
        # Throws ArithmeticException if and only if argument 2 is zero
        result = run_method_analysis(self.java_class, "alwaysThrows3")
        assert AnalysisResult.ArithmeticException in result

    def test_alwaysThrows4(self):
        # 2 arguments
        # throws AssertionError if argument 1 above -1 and argument 2 above 1
        # throws ArithmeticException if argument 2 is zero
        result = run_method_analysis(self.java_class, "alwaysThrows4")
        assert AnalysisResult.ArithmeticException in result
    
    def test_alwaysThrows5(self):
        # 2 arguments
        # throws ArithmeticException if i is zero or negative
        result = run_method_analysis(self.java_class, "alwaysThrows5")
        assert AnalysisResult.ArithmeticException in result
    
    def test_itDependsOnLattice1(self):
        # No arguments
        # Wrongly (but intended) throws ArithmeticException because we just translate 3 to plus.
        # Then when we subtract we do not know that we wont hit zero.
        result = run_method_analysis(self.java_class, "itDependsOnLattice1")
        assert AnalysisResult.ArithmeticException in result
    
    def test_itDependsOnLattice2(self):
        # No arguments
        # Wrongly (but intended) throws ArithmeticException because we just translate -1000 to minus.
        # Then when we add we do not know that we wont hit zero.
        result = run_method_analysis(self.java_class, "itDependsOnLattice2")
        assert AnalysisResult.ArithmeticException in result
    
    def test_itDependsOnLattice3(self):
        # No arguments
        # Wrongly (but intended) throws ArithmeticException be the subtraction can lead to zero.
        result = run_method_analysis(self.java_class, "itDependsOnLattice3")
        assert AnalysisResult.ArithmeticException in result
        
    def test_itDependsOnLattice4(self):
        # No arguments
        # Correctly throws ArithmeticException.
        result = run_method_analysis(self.java_class, "itDependsOnLattice4")
        assert AnalysisResult.ArithmeticException in result

    def test_neverThrows1(self):
        # No arguments
        # Never throws ArithmeticException
        result = run_method_analysis(self.java_class, "neverThrows1")
        assert AnalysisResult.ArithmeticException not in result
    
    def test_neverThrows2(self):
        # 1 argument
        # Throws AssertionError if i is 0
        # Throws AssertionError if i negative
        # Never throws ArithmeticException
        result = run_method_analysis(self.java_class, "neverThrows2")
        assert result.count(AnalysisResult.AssertionError) == 2
        assert AnalysisResult.ArithmeticException not in result
    
    def test_neverThrows3(self):
        # 2 arguments
        # Throws AssertionError if i is 0
        # Throws AssertionError if i negative
        # Throws AssertionError if j is positive
        # Throws AssertionError if j negative
        # Never throws ArithmeticException
        result = run_method_analysis(self.java_class, "neverThrows3")
        assert result.count(AnalysisResult.AssertionError) == 4
        assert AnalysisResult.ArithmeticException not in result
    
    def test_neverThrows4(self):
        # 1 argument
        # Throws AssertionError if i is 0
        # Throws AssertionError if i negative
        # Throws AssertionError if i postive
        # So this always throws an AssertionError
        result = run_method_analysis(self.java_class, "neverThrows4")
        assert result.count(AnalysisResult.AssertionError) == 3

    def test_neverThrows5(self):
        # 2 arguments
        # Never throws ArithmeticException
        result = run_method_analysis(self.java_class, "neverThrows5")
        assert AnalysisResult.ArithmeticException not in result

    def test_speedVsPrecision(self):
        # No arguments
        # Throws ArithmeticException
        # Since we are using plus, zero and minus the while loop leads to a fixed point.
        result = run_method_analysis(self.java_class, "speedVsPrecision")
        assert AnalysisResult.ArithmeticException in result

