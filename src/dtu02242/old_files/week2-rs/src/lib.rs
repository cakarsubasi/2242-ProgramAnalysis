use tree_sitter::{Parser, Node, TreeCursor};
use glob::glob;
use std::io::prelude::*;
use std::fs::File;
use std::path::PathBuf;
use std::env;
use std::fmt::Debug;

#[derive(PartialEq, PartialOrd)]
struct JavaClass {
    // class package
    pub package: String,
    // class name
    // although it is technically allowed
    // to have more than one top level class
    // in a java file, doing so causes other
    // problems with javac to the point that
    // we will likely never see it in practice
    pub name: Option<String>,
    // superclass if it has one
    pub superclass: Option<String>,
    // implementations
    pub implements: Vec<String>,
    // field dependencies
    pub fields: Vec<Field>,
    // non-static inner classes
    //pub composition: Vec<String>,
    // It should really be like this:
    pub composition: Vec<Box<JavaClass>>,
    // all other dependencies
    pub imports: Vec<String>,
    // text
    pub text: String,
}

#[derive(Debug, PartialEq, PartialOrd)]
struct FieldData {
    java_type: Option<JavaType>,
    fields: Vec<String>,
}

impl Into<Vec<Field>> for FieldData {
    fn into(self) -> Vec<Field> {
        let java_type = self.java_type.unwrap();
        self.fields.into_iter().map(|field| Field { java_type: java_type.to_owned(), field} ).collect()
    }
}

#[derive(Debug, PartialEq, PartialOrd)]
struct Field {
    java_type: JavaType,
    field: String,
}

#[derive(Debug, PartialEq, PartialOrd, Clone)]
enum JavaType {
    IntegralType(String),
    IdentifiedType(String),
    GenericType(String),
}

impl Debug for JavaClass {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("JavaClass")
        .field("package", &self.package)
        .field("name", &self.name)
        .field("superclass", &self.superclass)
        .field("implements", &self.implements)
        .field("fields", &self.fields)
        .field("composition", &self.composition)
        .field("dependencies", &self.imports).finish()
    }
}

impl JavaClass {
    fn new(text: &str) -> Self {
        Self {
            package: String::new(),
            name: None,
            superclass: None,
            implements: vec![],
            fields: vec![],
            composition: vec![],
            imports: vec![],
            text: String::from(text),
        }
    }

    fn new_from_tree(root_node: &Node, text: &str) -> Self {
        let mut java_class = Self::new(text);
        java_class.from_tree(root_node);
        java_class
    }

    fn from_tree(&mut self, root_node: &Node) {
        let mut cursor = root_node.walk();
        println!("{}", cursor.node().kind());

        //loop {
        //    if java_class.match_grammar(&mut cursor.node()) {
        //        cursor.goto_first_child(); continue;
        //    }
        //    if !cursor.goto_next_sibling() {
        //        break;
        //    }
        //}
        self.recursive_search(&mut cursor);

        // field_declaration (just use a regex)

        println!("{:#?}", self);
    }

    fn recursive_search(&mut self, cursor: &mut TreeCursor) {
        while self.match_grammar(&mut cursor.node()) {
            cursor.goto_first_child(); self.recursive_search(cursor)
        }
        if cursor.goto_next_sibling() {
            self.recursive_search(cursor);
        } 
    }

    ///
    /// @return: whether to continue searching
    fn match_grammar(&mut self, node: &Node) -> bool {
        match node.kind() {
            "program" => true,
            "package_declaration" => {self.retrieve_package(node); false}
            "import_declaration" => {self.retrieve_import(node); false}
            "class_declaration" => {self.retrieve_class_name(node); true}
            ";" | "{" | "}" => false,
            "line_comment" | "block_comment" => false,
            "class" => false,
            "modifiers" => false,
            // need to match identifiers against known patterns TODO
            "identifier" => false,
            // continue after finding class_body
            "class_body" => true,
            "super_interfaces" => {self.retrieve_interfaces(node); false}
            "method_declaration" => false,
            "field_declaration" => {self.retrieve_field(node); false}
            _ => {eprintln!("{} : {}", node.kind(), get_phrase_from_node(&self.text, node)); false}
        }
    }

    fn retrieve_package(&mut self, node: &tree_sitter::Node) {
        println!("Found package!");
        println!("{}", self.get_phrase_from_node(node));
        for node in node.named_children(&mut node.walk()) {
            match node.kind() {
                "package" => {}
                "scoped_identifier" => { 
                    let s = self.get_phrase_from_node(&node).to_owned();
                    self.package = s;
                    break;
                }
                _ => {
                    eprintln!("package: {} : {}", node.kind(), self.get_phrase_from_node(&node));
                }
            }
        }
    }

    fn retrieve_class_name(&mut self, node: &Node) {
        // find the first identifier
        println!("Found class name!");
        println!("{}", self.get_phrase_from_node(node));
        match self.name {
            // first class
            None => {
                for node in node.named_children(&mut node.walk()) {
                    match node.kind() {
                        "class" => {}
                        "modifiers" => {}
                        "identifier" => {
                            let s = self.get_phrase_from_node(&node).to_owned();
                            self.name = match self.name {
                                Some(_) => panic!("Whoops, two identifiers"),
                                None => Some(s),
                            };
                            break;
                        }
                        "class_body" => break,
                        _ => {
                            eprintln!("class_name: {} : {}", node.kind(), self.get_phrase_from_node(&node));
                        }
                    }
                }
            }
            // inner classes
            Some(_) => {
                let mut inner_class = JavaClass::new(&self.text);
                inner_class.package.push_str(&self.package);
                inner_class.package.push_str(".");
                inner_class.package.push_str(&self.name.as_ref().unwrap());
                inner_class.from_tree(node);
                self.composition.push(Box::new(inner_class));
            }
        }

    }

    fn retrieve_import(&mut self, node: &Node) {
        println!("Found import!");
        println!("{}", self.get_phrase_from_node(node));
        for node in node.named_children(&mut node.walk()) {
            match node.kind() {
                "import" => {}
                "asterisk" => {self.imports.last_mut().unwrap().push_str(".*")}
                "scoped_identifier" => {
                    self.imports.push(String::from(self.get_phrase_from_node(&node)));
                }
                _ => {
                    eprintln!("import: {} : {}", node.kind(), self.get_phrase_from_node(&node));
                }
            }
        }
    }

    fn retrieve_field(&mut self, node: &Node) {
        let mut field_data = FieldData {
            java_type: None,
            fields: vec![],
        };
        println!("Found field!");
        println!("{}", self.get_phrase_from_node(node));
        for node in node.named_children(&mut node.walk()) {
            match node.kind() {
                ";" | "," => {}
                "type_identifier" | "integral_type" | "generic_type" => {
                    let type_text = match field_data.java_type {
                        None => self.get_phrase_from_node(&node).to_string(),
                        _ => panic!("Need to change this function to cover this case")
                    };
                    field_data.java_type = match node.kind() {
                        "type_identifier" => Some(JavaType::IdentifiedType(type_text)),
                        "integral_type" => Some(JavaType::IntegralType(type_text)),
                        "generic_type" => Some(JavaType::GenericType((type_text))),
                        _ => { panic!("Uncovered cases.")}
                    }
                    
                }
                "variable_declarator" => {field_data.fields.push(self.get_phrase_from_node(&node).to_string())}
                "modifiers" => {}
                _ => {
                    eprintln!("field: {} : {}", node.kind(), self.get_phrase_from_node(&node));
                }
            }
        }
        self.fields = field_data.into();
    }

    fn retrieve_interfaces(&mut self, node: &Node) {
        println!("Found interface!");
        println!("{}", self.get_phrase_from_node(node));
        for node in node.named_children(&mut node.walk()) {
            match node.kind() {
                "implements" => {}
                "type_list" => { /* TODO */ }
                _ => {
                    eprintln!("{} : {}", node.kind(), self.get_phrase_from_node(&node));
                }
            }
        }
    }

    fn get_phrase_from_node<'a>(&'a self, node: &tree_sitter::Node) -> &'a str {
        let range = node.range();
        std::str::from_utf8(self.text.as_bytes().split_at(range.end_byte).0.split_at(range.start_byte).1).unwrap()
    }

}

fn find_all_java_files(directory: &str) -> Vec<PathBuf> {
    let mut file_names: Vec<_> = vec![];

    for entry in glob(format!("{}/**/*.java", directory).as_str()).unwrap() {
        match entry {
            Ok(path) => file_names.push(path),
            Err(e) => println!("{:?}", e),
        }
    }
    return file_names;
}

fn get_phrase_from_node<'a>(text: &'a str, node: &tree_sitter::Node) -> &'a str {
    let range = node.range();
    std::str::from_utf8(text.as_bytes().split_at(range.end_byte).0.split_at(range.start_byte).1).unwrap()
}

fn convert_to_dot(class_descriptions: &Vec<JavaClass>) -> String {
    format!("{:#?}", class_descriptions)
}

pub fn run() {
    let mut parser = Parser::new();
    parser.set_language(tree_sitter_java::language()).expect("Error loading grammar");

    let mut args = env::args();
    let directory;

    if args.len() == 1 {
        directory = ".".into();
    } else if args.len() == 2 {
        args.next();
        directory = args.next().unwrap();
    } else {
        panic!("Too many arguments");
    }

    let mut java_classes = vec![];

    let files = find_all_java_files(&directory);
    for file_name in files {
        let mut text = String::new();
        let mut file = File::open(&file_name).unwrap();
        file.read_to_string(&mut text).unwrap();
        let tree = parser.parse(&text, None).unwrap();
        println!("{}", file_name.display());

        java_classes.push(JavaClass::new_from_tree(&tree.root_node(), &text));
    }

    let mut dot = File::create("diagram.dot").unwrap();
    dot.write_all(convert_to_dot(&java_classes).as_bytes()).expect("failed to write");
}

mod grammar_test {

    use crate::*;

    #[test]
    fn test() {
        let text = &"";

        let result = JavaClass::new(text);
        assert_eq!(result, JavaClass { 
            package: todo!(), 
            name: todo!(), 
            superclass: todo!(), 
            implements: todo!(), 
            fields: todo!(), 
            composition: todo!(),
            imports: todo!(), 
            text: text.to_string() });
    }
}