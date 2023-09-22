from dtu02242.interpreter.interpreter import run_method, RefValue, ArrayValue, JavaError
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


class TestArray:
    with open("course-02242-examples/decompiled/dtu/compute/exec/Array.json", "r") as fp:
        json_dict = json.load(fp)
        java_class = JavaClass(json_dict=json_dict)

    def test_first(self):
        array = [0, 1, 3]
        assert run_method(self.java_class, "first", [array], None) == 0
        # array_empty = RefValue(ArrayValue([])) # TODO: Java still types empty arrays, so should handle that
        # assert run_method(self.java_class, "first", { "vals" : array }, None) == 0
        # No way to assert this right now without deciding on error handling
        # Best to use our own classes rather than relying on Python exceptions as Python 
        # exceptions can be inflexible

    def test_firstSafe(self):
        array = [1, 2, 3]
        assert run_method(self.java_class, "firstSafe", [array], None) == 1
        with pytest.raises(Exception) as ex:
            run_method(self.java_class, "firstSafe", [[]], None)
        assert str(ex.value) == "java/lang/AssertionError" 
        # need to decide on how to handle Java assert statements
        #array = RefValue(ArrayValue([]))
        #assert run_method(self.java_class, "firstSafe", { "vals" : array }, None) == IntValue(0)


    def test_access(self):        
        array = [0, 1, 3]
        assert run_method(self.java_class, "access", [0, array], None) == 0
        assert run_method(self.java_class, "access", [1, array], None) == 1
        assert run_method(self.java_class, "access", [2, array], None) == 3

    def test_newArray(self):
        assert run_method(self.java_class, "newArray", {}, None) == 1

    def test_newArrayOutOfBounds(self):
        with pytest.raises(Exception) as ex:
            run_method(self.java_class, "newArrayOutOfBounds", {}, None)
        assert str(ex.value) == "Index out of bounds"

    def test_accessSafe(self):
        array = [0, 1, 3]
        assert run_method(self.java_class, "accessSafe", [0, array], None) == 0
        assert run_method(self.java_class, "accessSafe", [1, array], None) == 1
        assert run_method(self.java_class, "accessSafe", [2, array], None) == 3
        with pytest.raises(Exception) as ex_1:
            run_method(self.java_class, "accessSafe", [3, array], None)
        assert str(ex_1.value) == "java/lang/AssertionError"
        with pytest.raises(Exception) as ex_2:
            run_method(self.java_class, "accessSafe", [-1, array], None)
        assert str(ex_2.value) == "java/lang/AssertionError"

    def test_bubbleSort(self):
        array = [3, 1, 2]
        run_method(self.java_class, "bubbleSort", [array], None)
        assert array == [1, 2, 3]

    def test_aWierdOneOutOfBounds(self):
        with pytest.raises(Exception) as ex:
            run_method(self.java_class, "aWierdOneOutOfBounds", {}, None)
        assert str(ex.value) == "Index out of bounds"

    def test_aWierdOneWithinBounds(self):
        assert run_method(self.java_class, "aWierdOneWithinBounds", {}, None) == 1

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
        assert run_method(self.java_class, "fib", [0]) == 1
        assert run_method(self.java_class, "fib", [1]) == 1
        assert run_method(self.java_class, "fib", [2]) == 2
        assert run_method(self.java_class, "fib", [3]) == 3
        assert run_method(self.java_class, "fib", [4]) == 5
        assert run_method(self.java_class, "fib", [5]) == 8
        assert run_method(self.java_class, "fib", [6]) == 13
        # after this point, the method should be so slow that it is a waste of time to test
        
        
