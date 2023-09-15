from glob import glob
from typing import List, Dict, Any, Optional, Tuple
import os
import json
from pathlib import Path
from enum import Enum

JsonDict = Dict[str, Any]
'''JSON files are dictionaries with string keys
and arbitrary values.'''

class AccessModifier(Enum):
    Private = 0
    Protected = 1
    Package_Private = 2
    Public = 3

uml_access = {
    AccessModifier.Private: "-",
    AccessModifier.Package_Private: "~",
    AccessModifier.Protected: "#",
    AccessModifier.Public: "+", 
}

class Definition():
    def __init__(self, name: str, is_static: bool, is_interface: bool, backing_dict=None):
        self.name: str = name # Fully qualified
        self.is_static: bool = is_static
        self.is_interface: bool = is_interface
        # self.is_abstract: bool = is_interface or is_abstract
        # self.access_modifier: AccessModifier
        self.inheritance : Optional[Definition] = None # Cem
        self.realization : List[Definition] = [] # Cem
        self.aggregation : List[Field] = [] # Oliver
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

class Field():
    def __init__(self, name: str, type_name: str, access_modifier: AccessModifier, is_static: bool):
        self.name : str = name
        self.type_name : str = type_name
        self.access_modifier : AccessModifier = access_modifier
        self.is_staic : bool = is_static

class Method():
    def __init__(self, name):
        self.name : str = name
        self.arguments : List[Tuple[Definition, str]] = []
        self.return_type : Optional[Definition] = None

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


def get_name(json_object: JsonDict) -> str:
    '''get fully qualified name as a str'''
    name: str = json_object['name'].replace('/', '.')
    return name


def get_super_class_name(json_object: JsonDict, ignore_java_lang_Object=True) -> Optional[str]:
    '''get fully qualified name of a super class as a str'''
    name = get_name(json_object['super'])
    if ignore_java_lang_Object and name == "java.lang.Object":
        return None
    else:
        return name


def get_interface_names(json_object: JsonDict) -> List[str]:
    '''get fully qualified names of the interfaces'''
    return [get_name(inner_dict) for inner_dict in json_object['interfaces']]

def get_field_type_name(json_object: JsonDict) -> str:
    '''get fully qualified names of the field types'''
    if "name" in json_object:
        nested = [get_field_type_name(inner["type"]) for inner in json_object["args"]]
        base_name = get_name(json_object)
        if len(nested) == 0:
            return base_name
        else:
            return f"{base_name}[{','.join(nested)}]"
    return json_object["base"]

def get_field_access(json_object: JsonDict) -> Tuple[bool, AccessModifier]:
    '''get access modifiers for field'''
    access_modifiers = json_object["access"]
    is_static = True if "static" in access_modifiers else False
    if "public" in access_modifiers:
        return (is_static, AccessModifier.Public)
    if "protected" in access_modifiers:
        return (is_static, AccessModifier.Protected)
    if "private" in access_modifiers:
        return (is_static, AccessModifier.Private)
    return (is_static, AccessModifier.Package_Private)

def get_fields(json_object: JsonDict) -> List[Tuple[str, str]]:
    '''get definition and fully qualified names of the fields'''
    fields = []
    for field in json_object["fields"]:
        field_name = field["name"]
        type_name = get_field_type_name(field["type"])
        is_static, acceess = get_field_access(field)
        fields.append(Field(field_name, type_name, acceess, is_static))
    return fields

def get_is_static(json_object: JsonDict) -> bool:
    '''return true if class is static'''
    return "static" in json_object['access']


def get_is_interface(json_object: JsonDict) -> bool:
    '''return true if class is an interface'''
    return "interface" in json_object['access']


def get_is_abstract(json_object: JsonDict) -> bool:
    '''return true if class is abstract'''
    return "abstract" in json_object['access']


def create_definition(json_object: JsonDict) -> Definition:
    '''Create a definition from the given JsonDict
    Not all fields are set within the class'''
    name = get_name(json_object)
    is_static = get_is_static(json_object)
    is_interface = get_is_interface(json_object)
    definition = Definition(name, is_static, is_interface)
    definition.backing_dict = json_object
    return definition


def set_superclass(definitions_dict: Dict[str, Definition]):
    '''
    Set superclass relations, ignores java.lang.Object as it is
    not useful information.
    '''
    for definition in definitions_dict.values():
        super_class_maybe = get_super_class_name(definition.backing_dict)
        if super_class_maybe is not None:
            definition.inheritance = definitions_dict[super_class_maybe]


def set_realization(definitions_dict: Dict[str, Definition]):
    '''
    Set interface relations.
    '''
    for definition in definitions_dict.values():
        interface_names = get_interface_names(definition.backing_dict)
        definition.realization = [definitions_dict[interface]
                                  for interface in interface_names]

def set_aggregation(definitions_dict: Dict[str, Definition]):
    for definition in definitions_dict.values():
        fields = get_fields(definition.backing_dict)
        definition.aggregation = fields

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
            sorted_fields =  sorted(definition.aggregation, key=lambda x: x.access_modifier.value, reverse=True)
            for field in sorted_fields:
                access = uml_access[field.access_modifier]
                if field.is_staic:
                    result += f"""<tr> <td align="left"><u> {access} {field.name} : {field.type_name} </u></td> </tr>\n"""
                else:
                    result += f"""<tr> <td align="left">{access} {field.name} : {field.type_name} </td> </tr>\n"""
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

def save_dot_text(definitions: List[Definition], output_file: Path):
    '''
    Save given list of definitions to a dot file
    '''
    text = create_graphviz_text(definitions)
    with open(output_file, "w+") as fp:
        print(text, file=fp)


def main():
    root_directory = Path(os.path.join("course-02242-examples"))
    output_file = Path("week3.dot")

    file_names: List[str] = find_files_by_type(
        root_dir=root_directory, file_type="json")
    file_texts: List[str] = [get_file_text(
        Path(file_name)) for file_name in file_names]
    json_objects: List[Dict[Any, Any]] = [
        json.loads(text) for text in file_texts]

    definitions = [create_definition(json_object)
                   for json_object in json_objects]
    print(definitions)

    definitions_dictionary = {
        definition.name: definition for definition in definitions}

    set_superclass(definitions_dictionary)
    set_realization(definitions_dictionary)
    set_aggregation(definitions_dictionary)

    save_dot_text(definitions=definitions, output_file=output_file)


if __name__ == "__main__":
    main()
