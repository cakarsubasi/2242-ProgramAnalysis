from glob import glob
from typing import List, Dict, Set
import re

# https://docs.oracle.com/javase/8/docs/api/java/lang/package-summary.html
DEFAULT_DECLARATIONS = ["String", "Integer", "Boolean", "Double", "Float", "Number", "Character", "Byte", "Short"]

PACKAGE_NAME = r"(?:package\s*)(.*\.\w+);"
FILE_NAME = r"(\w+)\.java"
STATIC_METHOD_NAME = r"static\s+\w+\s+(\w+)"
SINGLE_LINE_COMMENT = r"//.*"
INLINE_COMMENT = r"\/\*(?:.*)\*\/"
MULTI_LINE_COMMENT = r"/\*(?:.*\n)*.*\*/"
STRINGS = r'".*"'
FOLDER_IMPORTS = r"(?:import\s+)(.*\.\w+)\.\*;"
FILE_IMPORTS = r"(?:import\s+)(.*\.\w+);"
CLASS_OR_INTERFACE_NAME = r"(?:class|interface)\s+(\w+)"
INSTANCE_CREATION = r"\snew\s+(\w+)\([\w,]*\);"
GENERIC_TYPES = r"(\w+)\s*<\s*(\w*)\s*>(?!\s+\w+\s+\w+)"
ARRAY_DECLARATIONS = r"(\w+)\s*(?:\[\])+\s*(?:\w+)"

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

def construct_class_name_regex(class_names: Set[str]) -> str:
    return r"\b(" + "|".join(class_names) + r")\s+\w+"

def construct_generic_regex_finder(class_names: Set[str]) -> str:
    return fr"<({'|'.join(class_names)}(?:,\s*(?:{'|'.join(class_names)}))*)>\s+\w+\s+\w+\((\w+\s+\w+(?:,\s*\w+\s+\w+)*)\)"

def construct_static_method_regex(function_names: Set[str]) -> str:
    return r"\b(" + "|".join(function_names) + r")\s*\("
    

def create_graphviz_text(file_depends: Dict[str, Set[str]]):
    result = "digraph SourceGraph {"
    for file_name in file_depends.keys():
        result += f"""\n  "{file_name}" [label="{file_name}"];"""
    for file_name, dependencies in file_depends.items():
        for depedency in dependencies:
            result += f"""\n  "{file_name}" -> "{depedency}";"""
    result += "\n}"
    return result


def delete_comments(str: str) -> str:
    str = re.sub(SINGLE_LINE_COMMENT, "", str, count=0)
    str = re.sub(INLINE_COMMENT, "", str, count=0)
    str = re.sub(MULTI_LINE_COMMENT, "", str, count=0)
    str = re.sub(STRINGS, '""', str, count=0)
    return str


def find_declarations(str: str):
    matches = re.findall(CLASS_OR_INTERFACE_NAME, str)
    return set(matches)


def find_static_methods(str: str, file_name: str):
    matches = re.findall(STATIC_METHOD_NAME, str)
    return set(f"{file_name}.{match}" for match in matches)


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


def find_none_empty_matches_types(regex: str, content: str):
    matches = re.findall(regex, content)
    result = set()
    for group in matches:
        for match in [group] if isinstance(group, str) else group:
            if match == "":
                continue
            result.add(match)
    return set(result)


def find_dependency_from_imports(class_names, class_declarations, imported_files):
    result = set()
    for class_name in class_names:
        for imported_file in imported_files:
            for declaration in class_declarations[imported_file]:
                if declaration == class_name:
                    result.add(imported_file)
    return result

def find_generics_that_are_shadowing(generic_regex: str, content: str) -> Set[str]:
    generic_matches = re.findall(generic_regex, content)
    shadowing = set()
    for group in generic_matches:
        if len(group) < 2:
            continue
        
        generics = list(map(lambda x: x.strip(), group[0].split(",")))
        parameters = list(map(lambda x: x.strip().split(" ")[0].strip(), group[1].split(",")))
        for generic in generics:
            for parameter in parameters:
                if generic == parameter:
                    shadowing.add(generic)
    return shadowing


def main():
    # When working with a file name we use the fully qualified name
    file_content = find_files() # K: file name, V: contents with package name
    file_depends = {} # K: file name, V: set of dependencies
     # K: file name, V: set declarations
    class_declarations = { f"java.lang.{declaration}": set([declaration]) for declaration in DEFAULT_DECLARATIONS }
    imported_files = {} # K: file name, V: set of imported files (Including itself)

    static_methods = set()

    for k, v in file_content.items():
        file_content[k] = delete_comments(v)

    for k, v in file_content.items():
        declarations = find_declarations(v)
        class_declarations[k] = declarations
        static_methods = static_methods.union(find_static_methods(v, k))

    for k, v in file_content.items():
        folder_imports = find_imports_through_folders(v, file_content.keys())
        package_imports = find_imports_through_package(get_package_name(k), file_content.keys())
        default_imports = set([f"java.lang.{declaration}" for declaration in DEFAULT_DECLARATIONS])
        imported_files[k] = folder_imports.union(package_imports).union(default_imports)

    for k, v in file_content.items():
        file_depends[k] = find_file_imports(v)

    for k, v in file_content.items():
        matches = re.findall(construct_static_method_regex(static_methods), v)
        dependencies = set((".").join(match.split(".")[0:-1]) for match in matches)
        file_depends[k] = file_depends[k].union(dependencies)

    for k, v in file_content.items():
        for regex in [INSTANCE_CREATION, GENERIC_TYPES, ARRAY_DECLARATIONS]:
            matches = find_none_empty_matches_types(regex, v)
            dependencies = find_dependency_from_imports(matches, class_declarations, imported_files[k])
            file_depends[k] = file_depends[k].union(dependencies)

    for k, v in file_content.items():
        class_names = set()
        imports = imported_files[k]
        for imported in imports:
            class_names = class_names.union(class_declarations[imported])
        
        dynamic_class_regex = construct_class_name_regex(class_names)
        generic_regex = construct_generic_regex_finder(class_names)

        dynamic_matches = find_none_empty_matches_types(dynamic_class_regex, v)
        shadowing = find_generics_that_are_shadowing(generic_regex, v)

        for shadow in shadowing:
            dynamic_matches.discard(shadow)

        dependencies = find_dependency_from_imports(dynamic_matches, class_declarations, imported_files[k])
        file_depends[k] = file_depends[k].union(dependencies)


    for k, v in file_depends.items():
        file_depends[k].discard(k)

    print(create_graphviz_text(file_depends))


if __name__ == "__main__":
    main()

## like this List <foo> -> is not working
## same List< foo >
## if ( a < b && b > c)