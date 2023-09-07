use tree_sitter::{Parser, Language, Node};
use glob::glob;
use std::io::prelude::*;
use std::fs::File;
use std::marker::PhantomData;
use std::path::{Path, PathBuf};
use std::env;
use regex;

#[derive(Debug)]
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
    pub fields: Vec<String>,
    // non-static inner classes
    pub composition: Vec<String>,
    // all other dependencies
    pub dependencies: Vec<String>,
    // text
    pub text: String,
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
            dependencies: vec![],
            text: String::from(text),
        }
    }

    fn from_tree(tree: tree_sitter::Tree, text: &str) -> Self {
        let mut java_class = Self::new(text);
        let mut cursor = tree.walk();
        //cursor.goto_first_child();
        println!("{}", cursor.node().kind());

        loop {
            if java_class.match_grammar(&mut cursor.node()) {
                cursor.goto_first_child(); continue;
            }
            if !cursor.goto_next_sibling() {
                break;
            }
        }

        // field_declaration (just use a regex)

        java_class
    }

    ///
    /// @return: whether to continue searching
    fn match_grammar(&mut self, node: &tree_sitter::Node) -> bool {
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
        for node in node.children(&mut node.walk()) {
            match node.kind() {
                scoped_identifier => {}
                _ => {
                    eprintln!("{}", node.kind());
                    eprintln!("{}", self.get_phrase_from_node(&node));
                }
            }
        }
    }

    fn retrieve_class_name(&mut self, node: &Node) {
        // find the first identifier
        println!("Found class name!");
        println!("{}", self.get_phrase_from_node(node));
        for node in node.children(&mut node.walk()) {
            match node.kind() {
                _ => {
                    eprintln!("{} : {}", node.kind(), self.get_phrase_from_node(&node));
                }
            }
        }

    }

    fn retrieve_import(&mut self, node: &Node) {
        println!("Found import!");
        println!("{}", self.get_phrase_from_node(node));
        for node in node.children(&mut node.walk()) {
            match node.kind() {
                _ => {
                    eprintln!("{} : {}", node.kind(), self.get_phrase_from_node(&node));
                }
            }
        }
    }

    fn retrieve_field(&mut self, node: &Node) {
        println!("Found field!");
        println!("{}", self.get_phrase_from_node(node));
        for node in node.children(&mut node.walk()) {
            match node.kind() {
                _ => {
                    eprintln!("{} : {}", node.kind(), self.get_phrase_from_node(&node));
                }
            }
        }
    }

    fn retrieve_interfaces(&mut self, node: &Node) {
        println!("Found interface!");
        println!("{}", self.get_phrase_from_node(node));
        for node in node.children(&mut node.walk()) {
            match node.kind() {
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
    todo!()
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
    let mut text = String::new();
    for file_name in files {
        let mut file = File::open(&file_name).unwrap();
        file.read_to_string(&mut text).unwrap();
        let tree = parser.parse(&text, None).unwrap();
        println!("{}", file_name.display());

        java_classes.push(JavaClass::from_tree(tree, &text));
    }

    let mut dot = File::create("diagram.dot").unwrap();
    dot.write_all(convert_to_dot(&java_classes).as_bytes()).expect("failed to write");
}