import json
from typing import List, Dict, Any, Iterable, Optional, Type
from dataclasses import dataclass

@dataclass(frozen=False)
class BoundsArray:
    low: int
    upper: int
    elements = []
    null_object: bool
    reference : bool
    index : int

    @classmethod
    def from_type(cls, typename):
        if typename == "int":
            return BoundsArray(-(2**31), (2**31)-1, False, False, -1)
    
    @classmethod
    def create_array(cls, size, null, index):
        return BoundsArray(0, size, null, True, index)
    
    @classmethod
    def merge_states(cls, old_state, new_state):
        if old_state == None:
            return new_state


def analyse(m, abstract):
    locals = []
    stack = []

    bytecode = m["code"]["bytecode"]
    states = [None for b in m["code"]["bytecode"]]
    worklist = [0]

    states[0] = (locals, stack)

    for i, param in enumerate(m["params"]):
        if "kind" in param["type"]:
            if param["type"]["kind"] == "array":
                new_locals = abstract.create_array(0, True, i)
                locals.append(new_locals)
        elif "base" in param["type"]:
            locals.append(abstract.from_type(param["type"]["base"]))
    
    while worklist:
        job = worklist.pop()
        (l_local, l_stack), opr = states[job], bytecode[job]
        
        print(opr)

        if opr["opr"] == "load":
            l_stack.append(l_local[opr["index"]])
            job += 1
            res = abstract.merge_states(states[job], (l_local, l_stack))
            if res != states[job]:
                worklist.append(job)
            states[job] = res
        if opr["opr"] == "push":
            if opr["value"]["type"] == "integer":
                val = opr["value"]["value"]
                l_stack.append(BoundsArray(val,val, False, False, -1))
            job += 1
            res = abstract.merge_states(states[job], (l_local, l_stack))
            if res != states[job]:
                worklist.append(job)
            states[job] = res
        elif opr["opr"] == "array_load":
            index =  l_stack.pop()
            ref =  l_stack.pop()

            if (ref.null_object):
                print("Got null pointer exception at ", job)
            if (index.low < 0 or index.upper >= ref.upper):
                print("Got out of range exception at", job)

            arr_length = len(ref.elements)

            if (arr_length == 0 or index.upper > arr_length or index.low < 0):
                l_stack.append(BoundsArray(-(2**31), (2**31)-1, False, False, ref.index))
            else:
                l_stack.append(ref.elements[index.upper])
            
            job += 1
            res = abstract.merge_states(states[job], (l_local, l_stack))
            if res != states[job]:
                worklist.append(job)
            states[job] = res
        elif opr["opr"] == "return":
            l_stack.pop()
        elif opr["opr"] == "get":
            if opr["field"]["name"] == "$assertionsDisabled":
                l_stack.append(BoundsArray(0, 0, False, False, -1))
            job += 1
            res = abstract.merge_states(states[job], (l_local, l_stack))
            if res != states[job]:
                worklist.append(job)
            states[job] = res
        elif opr["opr"] == "ifz":
            val = l_stack.pop()
            zero = 0

            if opr["condition"] == "ne":
                if val.low != zero and val.upper != 0:
                    job = job + opr["target"]
                else:
                    job += 1

            res = abstract.merge_states(states[job], (l_local, l_stack))
            if res != states[job]:
                worklist.append(job)
            states[job] = res
        elif opr["opr"] == "arraylength":
            ref = l_stack.pop()

            if ref.null_object:
                print("Got null exception at ", job)

            l_stack.append(BoundsArray(ref.low, ref.upper, False, False, ref.index))
            job = job+1
            res = abstract.merge_states(states[job], (l_local, l_stack))
            if res != states[job]:
                worklist.append(job)
            states[job] = res
        elif opr["opr"] == "if":
            second = l_stack.pop()
            first = l_stack.pop()
            
            if opr["condition"] == "ge":
                job_first = opr["target"]
                local_copy = l_local
                if first.index != -1:
                    if second.low == second.upper:
                        local_copy[first.index].low = second.low
                        l_local[first.index].upper = second.low
                    else:
                        print("Not handled")
                job += 1
                res_first = abstract.merge_states(states[job_first], (local_copy, l_stack))
                res = abstract.merge_states(states[job], (l_local, l_stack))

                if res_first != states[job_first]:
                    worklist.append(job_first)
                if res != states[job]:
                    worklist.append(job)
                
                states[job]= res
                states[job_first] = res_first
        elif opr["opr"] == "new":
            if opr["class"] == "java/lang/AssertionError":
                pass
        elif opr["opr"] == "newarray":
            size = l_stack.pop()
            l_local.append(BoundsArray(0, size.low, False, True, len(l_local)))
            for i in range(0, size.low):
                l_local[-1].elements.append(None)
            l_stack.append(l_local[-1])
            job += 1
            res = abstract.merge_states(states[job], (l_local, l_stack))
            if res != states[job]:
                worklist.append(job)
            states[job]= res
        elif opr["opr"] == "dup":
            l_stack.append(l_stack[-1])
            job += 1
            res = abstract.merge_states(states[job], (l_local, l_stack))
            if res != states[job]:
                worklist.append(job)
            states[job]= res
        elif opr["opr"] == "array_store":
            val = l_stack.pop()
            index = l_stack.pop()
            ref = l_stack.pop()
            if ref.reference and index != -1:
                ref.elements[index.low] = val
            job += 1
            res = abstract.merge_states(states[job], (l_local, l_stack))
            if res != states[job]:
                worklist.append(job)
            states[job]= res
        elif opr["opr"] == "store":
            if opr["type"] == "ref":
                ref = l_stack.pop()
                l_local.append(ref)
            job += 1
            res = abstract.merge_states(states[job], (l_local, l_stack))
            if res != states[job]:
                worklist.append(job)
            states[job]= res


def getMethod(name, json):
    for method in json["methods"]:
        if method["name"] == name:
            return method

with open("Array.json", "r") as fp:
    res = json.load(fp)
    
    first = getMethod("first", res)
    access = getMethod("access", res)
    first_safe = getMethod("firstSafe", res)
    new_array = getMethod("newArray", res)
    new_array_out = getMethod("newArrayOutOfBounds", res)
    weird = getMethod("aWierdOneOutOfBounds", res)

    # analyse(first, BoundsArray)
    # analyse(access, BoundsArray)
    # analyse(first_safe, BoundsArray)
    # analyse(new_array, BoundsArray)
    # analyse(new_array_out, BoundsArray)
    analyse(weird, BoundsArray)