from interpreter.parser import JavaClass, find_files_by_type, get_file_text
from interpreter.interpreter import run_method
import os
from pathlib import Path
import json


root = Path(os.path.join("course-02242-examples/decompiled/dtu/compute/exec"))

file_names = find_files_by_type(
        root_dir=root, file_type="json")
file_texts = [get_file_text(
    Path(file_name)) for file_name in file_names]
json_objects = [
    json.loads(text) for text in file_texts]

java_classes = [JavaClass(jsonDict) for jsonDict in json_objects]

run_method(java_classes[0], "noop", {})
run_method(java_classes[0], "zero", {})

