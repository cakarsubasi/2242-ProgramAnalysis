from dtu02242.interpreter.interpreter import run_method, IntValue, RefValue, ArrayValue, JavaError
from dtu02242.interpreter.parser import get_file_text, find_files_by_type, JavaClass
from pathlib import Path
import json
import pytest

class TestErrors:
    pass

class TestSimple:
    with open("course-02242-examples/decompiled/dtu/compute/exec/Simple.json", "r") as fp:
        json_dict = json.load(fp)
        java_class = JavaClass(json_dict=json_dict)

    def test_noop(self):
        result = run_method(self.java_class, "noop", {}, None)
        assert result is None

    def test_zero(self):
        result = run_method(self.java_class, "zero", {}, None)
        assert result == 0

    def test_hundredAndTwo(self):
        result = run_method(self.java_class, "hundredAndTwo", {}, None)
        assert result == 102

    def test_identity(self):
        assert run_method(self.java_class, "identity", [1], None) == 1
        assert run_method(self.java_class, "identity", [2], None) == 2
        assert run_method(self.java_class, "identity", [-5], None) == -5

    def test_add(self):
        # Sanity check
        assert run_method(self.java_class, "add", [1, 1], None) == 2
        assert run_method(self.java_class, "add", [0, 1], None) == 1
        assert run_method(self.java_class, "add", [-1, 1], None) == 0

    def test_min(self):
        assert run_method(self.java_class, "min", [-1, 1], None) == -1
        assert run_method(self.java_class, "min", [1, -1], None) == -1
        assert run_method(self.java_class, "min", [1, 1], None) == 1

    def test_factorial(self):
        assert run_method(self.java_class, "factorial", [1], None) == 1
        assert run_method(self.java_class, "factorial", [2], None) == 2
        assert run_method(self.java_class, "factorial", [3], None) == 6
        assert run_method(self.java_class, "factorial", [4], None) == 24
        assert run_method(self.java_class, "factorial", [5], None) == 120
        assert run_method(self.java_class, "factorial", [6], None) == 720


@pytest.mark.skip(reason="First get TestSimple working")
class TestArray:
    with open("course-02242-examples/decompiled/dtu/compute/exec/Array.json", "r") as fp:
        json_dict = json.load(fp)
        java_class = JavaClass(json_dict=json_dict)

    def test_first(self):
        array = RefValue(ArrayValue([IntValue(0), IntValue(1), IntValue(3)]))
        assert run_method(self.java_class, "first", { "vals" : array }, None) == IntValue(0)
        array_empty = RefValue(ArrayValue([])) # TODO: Java still types empty arrays, so should handle that
        # assert run_method(self.java_class, "first", { "vals" : array }, None) == IntValue(0)
        # No way to assert this right now without deciding on error handling
        # Best to use our own classes rather than relying on Python exceptions as Python 
        # exceptions can be inflexible

    def test_firstSafe(self):
        array = RefValue(ArrayValue([IntValue(0), IntValue(1), IntValue(3)]))
        assert run_method(self.java_class, "firstSafe", { "vals" : array }, None) == IntValue(0)
        # need to decide on how to handle Java assert statements
        #array = RefValue(ArrayValue([]))
        #assert run_method(self.java_class, "firstSafe", { "vals" : array }, None) == IntValue(0)


    def test_access(self):        
        array = RefValue(ArrayValue([IntValue(0), IntValue(1), IntValue(3)]))
        assert run_method(self.java_class, "access", { "i": IntValue(0) , "vals" : array }, None) == IntValue(0)
        assert run_method(self.java_class, "access", { "i": IntValue(1) , "vals" : array }, None) == IntValue(1)
        assert run_method(self.java_class, "access", { "i": IntValue(2) , "vals" : array }, None) == IntValue(3)

    def test_newArray(self):
        assert run_method(self.java_class, "newArray", {}, None) == IntValue(1)

    def test_newArrayOutOfBounds(self):
        assert run_method(self.java_class, "newArray", {}, None) is JavaError

    def test_accessSafe(self):
        array = RefValue(ArrayValue([IntValue(0), IntValue(1), IntValue(3)]))
        assert run_method(self.java_class, "accessSafe", { "i": IntValue(0) , "vals" : array }, None) == IntValue(0)
        assert run_method(self.java_class, "accessSafe", { "i": IntValue(1) , "vals" : array }, None) == IntValue(1)
        assert run_method(self.java_class, "accessSafe", { "i": IntValue(2) , "vals" : array }, None) == IntValue(3)
        assert run_method(self.java_class, "accessSafe", { "i": IntValue(3) , "vals" : array }, None) is JavaError
        assert run_method(self.java_class, "accessSafe", { "i": IntValue(-1) , "vals" : array }, None) is JavaError

    def test_bubbleSort(self):
        array = RefValue(ArrayValue([IntValue(3), IntValue(1), IntValue(2)]))
        result = run_method(self.java_class, "bubbleSort", {"vals": array}, None)
        assert result == RefValue(ArrayValue([IntValue(1), IntValue(2), IntValue(3)]))

    def test_aWierdOneOutOfBounds(self):
        assert run_method(self.java_class, "aWierdOneOutOfBounds", {}, None) is JavaError

    def test_aWierdOneWithinBounds(self):
        assert run_method(self.java_class, "aWierdOneOutOfBounds", {}, None) == IntValue(1)

@pytest.mark.skip(reason="First get TestSimple working")
class TestCalls:
    with open("course-02242-examples/decompiled/dtu/compute/exec/Calls.json", "r") as fp:
        json_dict = json.load(fp)
        java_class = JavaClass(json_dict=json_dict)

    @pytest.mark.skip(reason="Decide on how to track output")
    def test_helloWorld(self):
        # Need to decide on how to handle stdin and stdout first
        # For stdout, I propose passing a variable that will just collect
        # the output which we can then inspect
        assert run_method(self.java_class, "helloWorld", {}, None) is None

    def test_fib(self):
        assert run_method(self.java_class, "fib", {"n" : IntValue(0)}) == IntValue(1)
        assert run_method(self.java_class, "fib", {"n" : IntValue(1)}) == IntValue(1)
        assert run_method(self.java_class, "fib", {"n" : IntValue(2)}) == IntValue(2)
        assert run_method(self.java_class, "fib", {"n" : IntValue(3)}) == IntValue(3)
        assert run_method(self.java_class, "fib", {"n" : IntValue(4)}) == IntValue(5)
        assert run_method(self.java_class, "fib", {"n" : IntValue(5)}) == IntValue(8)
        assert run_method(self.java_class, "fib", {"n" : IntValue(6)}) == IntValue(13)
        # after this point, the method should be so slow that it is a waste of time to test
        
        
