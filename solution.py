from glob import glob
from typing import List, Dict, Set
import re

PACKAGE_NAME = r"(?:package\s*)(.*\.\w+);"
FILE_NAME = r"(\w+)\.java"
SINGLE_LINE_COMMENT = r"//.*"
MULTI_LINE_COMMENT = r"/\*(?:.*\n)*.*\*/"
FOLDER_IMPORTS = r"(?:import\s+)(.*\.\w+)\.\*;"
FILE_IMPORTS = r"(?:import\s+)(.*\.\w+);"
CLASS_OR_INTERFACE_NAME = r"(?:class|interface)\s+(\w+)"
INSTANCE_CREATION = r"new\s+(\w+)\([\w,]*\);"

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

def find_imports_through_folders(str: str, file_names: List[str]):
    matches = re.findall(FOLDER_IMPORTS, str)
    result = set()
    for match in matches:
        for file_name in file_names:
            if file_name.startswith(match):
                result.add(file_name)
    return result

def find_imports_through_package(package_name: str, file_names: List[str]):
    result = set()
    for file_name in file_names:
        if file_name.startswith(package_name):
            result.add(file_name)
    return result

def find_file_imports(str: str):
    matches = re.findall(FILE_IMPORTS, str)
    return set(matches)

def find_instance_creations(str: str):
    matches = re.findall(INSTANCE_CREATION, str)
    return set(matches)

def find_declarations(str: str):
    matches = re.findall(CLASS_OR_INTERFACE_NAME, str)
    return set(matches)

def find_dependency_from_imports(class_names, class_declarations, imported_files):
    result = set()
    for class_name in class_names:
        for imported_file in imported_files:
            for declaration in class_declarations[imported_file]:
                if declaration == class_name:
                    result.add(imported_file)
    return result

def create_graphviz_text(file_depends: Dict[str, Set[str]]):
    result = "digraph SourceGraph {"
    for file_name in file_depends.keys():
        result += f"""\n  "{file_name}" [label="{file_name}"];"""
    for file_name, dependencies in file_depends.items():
        for depedency in dependencies:
            result += f"""\n  "{file_name}" -> "{depedency}";"""
    result += "\n}"
    return result

def main():
    # When working with a file name we use the fully qualified name
    file_content = find_files() # K: file name, V: contents with package name
    file_depends = {} # K: file name, V: set of dependencies
    class_declarations = {} # K: file name, V: set declarations
    imported_files = {} # K: file name, V: set of imported files (Including itself)

    for k, v in file_content.items():
        file_content[k] = delete_comments(v)

    for k, v in file_content.items():
        declarations = find_declarations(v)
        class_declarations[k] = declarations

    for k, v in file_content.items():
        folder_imports = find_imports_through_folders(v, file_content.keys())
        package_imports = find_imports_through_package(get_package_name(k), file_content.keys())
        imported_files[k] = folder_imports.union(package_imports)

    for k, v in file_content.items():
        file_depends[k] = find_file_imports(v)

    for k, v in file_content.items():
        classes = find_instance_creations(v)
        dependencies = find_dependency_from_imports(classes, class_declarations, imported_files)
        file_depends[k] = file_depends[k].union(dependencies)

    for k, v in file_depends.items():
        file_depends[k].discard(k)

    print(create_graphviz_text(file_depends))


if __name__ == "__main__":
    main()


