from pathlib import Path
from typing import List, Dict, Any, Iterable, Optional, Type
from glob import glob


JsonTypes = str | bool | float | List['JsonTypes']
JsonDict = Dict[str, 'JsonDict | JsonTypes' ]

class JavaClass:
    name: str
    json_dict: JsonDict

    def __init__(self, json_dict: JsonDict) -> None:
        self.name = json_dict['name']
        self.json_dict = json_dict

    def get_methods(self) -> List[JsonDict]:
        methods: List[JsonDict] = self.json_dict["methods"]
        return methods
    
    def get_method(self, name: str) -> JsonDict:
        methods = self.get_methods()
        for method in methods:
            if method["name"] == name:
                return method
        raise Exception("Method {name} not found in {self}")
    
    def __str__(self) -> str:
        return f"{self.name}"
    
    def __repr__(self) -> str:
        return self.json_dict["name"]

class JavaProgram:
    _java_classes: Dict[str, JavaClass]

    def __init__(self, java_classes: Iterable[JavaClass], entry_point: Optional[str]=None) -> None:
        self._java_classes = {str(java_class): java_class for java_class in java_classes}
        self._entry_point = entry_point

    def get_class(self, class_name: str) -> JavaClass | None:
        return self._java_classes.get(class_name)
    
    def __str__(self) -> str:
        return str(self._java_classes)

def find_files_by_type(root_dir: Path, file_type: str) -> List[str]:
    '''Get the str path of all files in a given root directory of a given file type'''
    file_names = glob(f"{root_dir}/**/*.{file_type}", recursive=True)
    return file_names


def get_file_text(file: Path) -> str:
    '''Get text from a file in the given path'''
    try:
        with open(file) as fp:
            content = fp.read()
    except OSError as err:
        print(f"Error opening file: {err}")
        exit(-1)
    return content