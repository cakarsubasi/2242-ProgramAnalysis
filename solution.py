from glob import glob
from typing import List, Dict, Tuple
import re

PACKAGE_NAME = r"(?:package\s*)(.*\.\w+);"
FILE_NAME = r"(\w+)\.java"
SINGLE_LINE_COMMENT = r"//.*"
MULTI_LINE_COMMENT = r"/\*(?:.*\n)*.*\*/"
FOLDER_IMPORTS = r"(?:import\s*)(.*\.\w+)\.\*;"
FILE_IMPORTS = r"(?:import\s*)(.*\.\w+);"
CLASS_OR_INTERFACE_NAME = r"(?:class|interface)\s+(\w+)"

def find_files() -> Dict[str, str]:
    file_names = glob("**/*.java", recursive=True)
    files: Dict[str, str] = {}

    for file in file_names:
        with open(file) as fp:
            # ASSUMPTION: We are only working with files that have a package line
            # https://docs.oracle.com/javase%2Ftutorial%2F/java/package/createpkgs.html
            first_line = fp.readline()
            package_name = re.findall(PACKAGE_NAME, first_line)[0]
            file_name = re.findall(FILE_NAME, file)[0]
            content = fp.read()
            files[f"{package_name}.{file_name}"] = content

    return files

def get_package_name(file_name: str) -> str:
    return ".".join(file_name.split(".")[0:-1])

def delete_comments(str: str) -> str:
    str = re.sub(SINGLE_LINE_COMMENT, "", str, count=0)
    str = re.sub(MULTI_LINE_COMMENT, "", str, count=0)
    return str

def delete_strings(str: str) -> str:
    pass

def find_imports_through_folders(str: str, file_names: [str]):
    matches = re.findall(FOLDER_IMPORTS, str)
    result = set()
    for match in matches:
        for file_name in file_names:
            if file_name.startswith(match):
                result.add(file_name)
    return result

def find_imports_through_package(package_name: str, file_names: [str]):
    result = set()
    for file_name in file_names:
        if file_name.startswith(package_name):
            result.add(file_name)
    return result

def find_file_imports(str: str):
    matches = re.findall(FILE_IMPORTS, str)
    return matches

def find_declarations(str: str):
    matches = re.findall(CLASS_OR_INTERFACE_NAME, str)
    return matches


def main():
    # When working with a file/class/interface name we use the fully qualified name
    file_content = find_files() # K: file name, V: contents with package name
    file_depends = {} # K: file name, V: list of dependencies
    class_declarations = {} # K: declaration, V: file name
    imported_files = {} # K: file name, V: set of imported files (Including itself)

    for k, v in file_content.items():
        file_content[k] = delete_comments(v)

    for k, v in file_content.items():
        package_name = get_package_name(k)
        declarations = find_declarations(v)
        for declaration in declarations:
            class_declarations[f"{package_name}.{declaration}"] = k # Fully qualified

    for k, v in file_content.items():
        folder_imports = find_imports_through_folders(v, file_content.keys())
        package_imports = find_imports_through_package(get_package_name(k), file_content.keys())
        imported_files[k] = folder_imports.union(package_imports)

    for k, v in file_content.items():
        file_depends[k] = find_file_imports(v)

    for k, v in file_content.items():
        print(k)
        print(v)

    print(file_depends)
    print(class_declarations)


if __name__ == "__main__":
    main()


