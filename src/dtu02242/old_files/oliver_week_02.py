from tree_sitter import Language, Parser, Node
from glob import glob
from typing import List, Dict, Set, Tuple, Optional, Any
import re
from enum import Enum

JsonDict = Dict[str, Any]
'''JSON files are dictionaries with string keys
and arbitrary values.'''

# https://docs.oracle.com/javase/8/docs/api/java/lang/package-summary.html
DEFAULT_DECLARATIONS = ["String", "Integer", "Boolean", "Double", "Float", "Number", "Character", "Byte", "Short"]

PACKAGE_NAME = r"(?:package\s*)(.*\.\w+);"
FILE_NAME = r"(\w+)\.java"
FOLDER_IMPORTS = r"(?:import\s+)(.*\.\w+)\.\*;"
FILE_IMPORTS = r"(?:import\s+)(.*\.\w+);"

class AccessModifier(Enum):
    Private = 0
    Protected = 1
    Package_Private = 2
    Public = 3

class Definition():
    def __init__(self, name: str, is_static: bool, is_interface: bool, backing_dict=None):
        self.name: str = name # Fully qualified
        self.is_static: bool = is_static
        self.is_interface: bool = is_interface
        # self.is_abstract: bool = is_interface or is_abstract
        # self.access_modifier: AccessModifier
        self.inheritance : Optional[Definition] = None # Cem
        self.realization : List[Definition] = [] # Cem
        self.aggregation : List[Tuple[Definition, str]] = [] # Oliver
        self.composition : List[Definition] = [] # Franciszek
        self.dependencies : List[Definition] = [] # Franciszek
        self.methods : List[Method] = [] # Maks
        self.file_name : str = "" # Used for classes nested inside other files
        
        self.backing_dict : JsonDict = backing_dict

    def __str__(self) -> str:
        return self.name
        #return \
        #f"Java Definition: {self.name}\n"\
        #f"    static: {self.is_static}\n"\
        #f"    interface: {self.is_interface}\n"
    
    def __repr__(self) -> str:
        # lazy
        return str(self)

def create_definition() -> Definition:
    pass


class Method():
    def __init__(self, name):
        self.name : str = name
        self.arguments : List[Tuple[Definition, str]] = []
        self.return_type : Optional[Definition] = None


def find_files() -> Dict[str, str]:
    file_names = glob("course-02242-examples/**/extra/*.java", recursive=True)
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


def create_graphviz_text(definitions: List[Definition]):
    result = "digraph UML_Class_diagram  {"
    for definition in definitions:
        if definition.inheritance is not None:
            result += "edge [dir=back arrowtail=empty style=\"\"]\n"
            result += f'"{definition.inheritance}" -> "{definition.name}" [label=inheritance]\n'
        
        if len(definition.realization) > 0:
            result += "edge [dir=back arrowtail=empty style=dashed]\n"
            for interface in definition.realization:
                result += f'"{interface}" -> "{definition.name}" [label=realization]'
        
        if len(definition.composition) > 0:
            result += "edge [dir=back arrowtail=diamond]\n"
            for inner_class in definition.composition:
                result += f'"{definition.name}":"{inner_class.name}" -> "{inner_class.name}" [label=composition]'

        result += f"""
        "{definition.name}" [
            shape=plain
            label=<<table border="0" cellborder="1" cellspacing="0" cellpadding="4">
                <tr> <td> <b>"{definition.name}"</b> </td> </tr>
        """
        if len(definition.aggregation) > 0 or len(definition.composition) > 0:
            result += """
                    <tr> <td>
                    <table align="left" border="0" cellborder="0" cellspacing="0" >"""
            for field in definition.aggregation:
                result += f"""<tr> <td align="left">+ {field[1]} : {field[0]} </td> </tr>\n"""
            for inner_class in definition.composition:
                result += f"""<tr> <td port="{inner_class.name}" align="left" >- "{inner_class.name}"</td> </tr>\n"""
            result += """
                </table>
                </td> </tr>"""
        result += """
            </table>>
        ]
        """
    result += "\n}"
    return result


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


def find_full_class_name(class_name, class_declarations, imported_files):
    for imported_file in imported_files:
        for declaration in class_declarations[imported_file]:
            if declaration == class_name:
                file_name = imported_file.split(".")[-1]
                if file_name == class_name:
                    return imported_file
                return f"{imported_file}.{class_name}"
    return class_name


def get_parser():
    FILE = "./languages.so" # the ./ is important
    Language.build_library(FILE, ["tree-sitter-java"])
    JAVA_LANGUAGE = Language(FILE, "java")
    parser = Parser()
    parser.set_language(JAVA_LANGUAGE)
    return parser


def parse_interfaces(interface_node: Node):
    result = []
    interfaces_child = next(x for x in interface_node.children if x.type == "type_list")
    for child in interfaces_child.named_children:
        if "type" in child.type:
            result.append(child.text.decode("utf8"))
    return result


def parse_inheritance(base_class_node: Node):
    type_indentifier = next(x for x in base_class_node.children if x.type == "type_identifier")
    return type_indentifier.text.decode("utf8")


def parse_field(field_node: Node):
    field_type =  next(x for x in field_node.named_children if "type" in x.type).text.decode("utf8")
    field_name_child = next(x for x in field_node.named_children if x.type == "variable_declarator")
    field_name = next(x for x in field_name_child.named_children if x.type == "identifier").text.decode("utf8")
    return (field_type, field_name)


def parse_class_body(result: Definition, class_body_node: Node):
    inner_classes = []
    for child in class_body_node.named_children:
        if child.type == "field_declaration":
            field_info = parse_field(child)
            result.aggregation.append(field_info)
        elif child.type == "class_declaration":
            inner_class = walk_class_tree(child)[0]
            if not inner_class.is_static:
                result.composition.append(inner_class)
            inner_classes.append(inner_class)
    return inner_classes


def walk_class_tree(class_node: Node):
    class_name = next(x for x in class_node.children if x.type == "identifier").text.decode("utf8")
    is_static = "static" in next(x for x in class_node.children if x.type == "modifiers").text.decode("utf8")
    outer_class = Definition(class_name, is_static, False)
    result = [outer_class]
    for child in class_node.children:
        if child.type == "super_interfaces":
            outer_class.realization = parse_interfaces(child)
        if child.type == "superclass":
            outer_class.inheritance = parse_inheritance(child)
        elif child.type == "class_body":
            inner_classes = parse_class_body(outer_class, child)
            result += inner_classes
    return result


def walk_interface_tree(interface_node: Node):
    class_name = next(x for x in interface_node.children if x.type == "identifier").text.decode("utf8")
    is_static = "static" in next(x for x in interface_node.children if x.type == "modifiers").text.decode("utf8")
    interface = Definition(class_name, is_static, True)
    return [interface]


def walk_file_tree(parser: Parser, content: str):
    tree = parser.parse(content.encode("utf8"))
    result = []
    for child in tree.root_node.children:
        if child.type == "class_declaration":
            classes = walk_class_tree(child)
            result += classes
        elif child.type == "interface_declaration":
            interfaces = walk_interface_tree(child)
            result += interfaces
    return result
    

def main():
    # When working with a file name we use the fully qualified name
    file_content = find_files() # K: file name, V: contents with package name
    file_depends = {} # K: file name, V: set of dependencies
     # K: file name, V: set declarations
    class_declarations = { f"java.lang.{declaration}": set([declaration]) for declaration in DEFAULT_DECLARATIONS }
    imported_files = {} # K: file name, V: set of imported files (Including itself)
    
    for k, v in file_content.items():
        folder_imports = find_imports_through_folders(v, file_content.keys())
        package_imports = find_imports_through_package(get_package_name(k), file_content.keys())
        default_imports = set([f"java.lang.{declaration}" for declaration in DEFAULT_DECLARATIONS])
        imported_files[k] = folder_imports.union(package_imports).union(default_imports)

    parser = get_parser()
    definitions: List[Definition] = [] 
    for file_name, content in file_content.items():
        found_definitions = walk_file_tree(parser, content)
        class_declarations[file_name] = set(x.name for x in found_definitions)
        for definition in found_definitions:
            definition.file_name = file_name
            definition.name = f"{get_package_name(file_name)}.{definition.name}"
        definitions += found_definitions
    
    for definition in definitions:
        imports = imported_files[definition.file_name]
        definition.inheritance = find_full_class_name(definition.inheritance, class_declarations, imports)
        for i in range(len(definition.realization)):
            definition.realization[i] = find_full_class_name(definition.realization[i], class_declarations, imports)

    text = create_graphviz_text(definitions)
    with open("oliver_week_02.dot", "w+") as f:
        print(text, file=f)

if __name__ == "__main__":
    main()