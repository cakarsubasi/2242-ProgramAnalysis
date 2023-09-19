from pathlib import Path
from typing import List, Dict, Any, Iterable, Optional
from glob import glob

class JavaClass:
    def __init__(self, json_dict: Dict[str, Any]) -> None:
        pass

    def get_methods(self) -> List[Dict[str, Any]]:
        raise NotImplementedError

class JavaProgram:
    def __init__(self, java_classes: Iterable[JavaClass], entry_point: Optional[str]) -> None:
        pass

    def get_class(self, class_name: str) -> JavaClass:
        raise NotImplementedError




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