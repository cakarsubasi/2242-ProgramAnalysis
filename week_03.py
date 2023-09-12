import oliver_week_02 as dot
from glob import glob
from typing import List, Dict, Any, Optional
import os
import json
from pathlib import Path

JsonDict = Dict[str, Any]
'''JSON files are dictionaries with string keys
and arbitrary values.'''


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


def get_is_static(json_object: JsonDict) -> bool:
    '''return true if class is static'''
    return "static" in json_object['access']


def get_is_interface(json_object: JsonDict) -> bool:
    '''return true if class is an interface'''
    return "interface" in json_object['access']


def get_is_abstract(json_object: JsonDict) -> bool:
    '''return true if class is abstract'''
    return "abstract" in json_object['access']


def create_definition(json_object: JsonDict) -> dot.Definition:
    '''Create a definition from the given JsonDict
    Not all fields are set within the class'''
    name = get_name(json_object)
    is_static = get_is_static(json_object)
    is_interface = get_is_interface(json_object)
    definition = dot.Definition(name, is_static, is_interface)
    definition.backing_dict = json_object
    return definition


def set_superclass(definitions_dict: Dict[str, dot.Definition]):
    '''
    Set superclass relations, ignores java.lang.Object as it is
    not useful information.
    '''
    for definition in definitions_dict.values():
        super_class_maybe = get_super_class_name(definition.backing_dict)
        if super_class_maybe is not None:
            definition.inheritance = definitions_dict[super_class_maybe]


def set_realization(definitions_dict: Dict[str, dot.Definition]):
    '''
    Set interface relations.
    '''
    for definition in definitions_dict.values():
        interface_names = get_interface_names(definition.backing_dict)
        definition.realization = [definitions_dict[interface]
                                  for interface in interface_names]


def save_dot_text(definitions: List[dot.Definition], output_file: Path):
    '''
    Save given list of definitions to a dot file
    '''
    text = dot.create_graphviz_text(definitions)
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

    save_dot_text(definitions=definitions, output_file=output_file)


if __name__ == "__main__":
    main()
