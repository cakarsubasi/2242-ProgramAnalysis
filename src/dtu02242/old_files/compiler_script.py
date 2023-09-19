#!/usr/bin/python3

import subprocess
import argparse


def main():
    parser = argparse.ArgumentParser(
        prog='jvm2json-automator',
        description='Find java files from the root directory, compile them, and then convert them to json files using jvm2json.'
    )

    parser.add_argument(
        'root_directory', help='root directory to search for .java files')
    args = parser.parse_args()

    root_directory = args.root_directory

    # Find java files
    result = subprocess.run(
        ["find", f"{root_directory}", "-name", "*.java"], capture_output=True)
    java_files = result.stdout.split()

    # Compile java files
    _ = subprocess.run(["javac"] + java_files, capture_output=True)

    # Find class files
    result = subprocess.run(
        ["find", f"{root_directory}", "-name", "*.class"], capture_output=True)
    class_files = result.stdout.split()

    # Create json file names matching class files
    json_files = [string.replace(b".class", b".json")
                  for string in class_files]

    # Run jvm2json for each class file
    for c, j in zip(class_files, json_files):
        subprocess.run(["jvm2json", "-s", c, "-t", j])

    print("done")


if __name__ == "__main__":
    main()
