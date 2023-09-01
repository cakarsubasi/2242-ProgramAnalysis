from glob import glob
from typing import List, Dict, Tuple
import re

SINGLE_LINE = r"//.*"
MULTI_LINE = r"/\*(?:.*\n)*.*\*/"
FILE_IMPORTS = "(?:import\s*)(.*\.\w+);"
CLASS_OR_INTERFACE_NAME = "(?:class|interface)\s+(\w+)"

def find_files() -> Dict[str, str]:
    file_names = glob("**/*.java", recursive=True)
    file_content: Dict[str, str] = {}

    for file in file_names:
        with open(file) as fp:
            file_content[file] = fp.read()

    return file_content

def fix_file_name():
    pass

def delete_comments(str: str) -> str:
    str = re.sub(SINGLE_LINE, "", str, count=0)
    str = re.sub(MULTI_LINE, "", str, count=0)
    return str

def delete_strings(str: str) -> str:
    pass

def matching_imports(str: str):
    matches = re.findall(FILE_IMPORTS, str)
    return matches

def matching_declarations(str: str):
    matches = re.findall(CLASS_OR_INTERFACE_NAME, str)
    return matches


def main():
    file_content = find_files() # K: file name, V: contents
    file_depends = {} # K: file name, V: list of dependencies
    class_declarations = {} # K: declaration (fully qualified), V: file name

    for k, v in file_content.items():
        file_content[k] = delete_comments(v)

    for k, v in file_content.items():
        file_depends[k] = matching_imports(v)
        matches = matching_declarations(v, k)
        for match in matches:
            class_declarations[match] = k # Fully qualified

    for k, v in file_content.items():
        print(k)
        print(v)

    print(file_depends)
    print(class_declarations)


if __name__ == "__main__":
    main()


