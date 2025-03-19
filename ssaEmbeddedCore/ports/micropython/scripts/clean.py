import ast
import astor
import sys
import os


def remove_docstrings(input_file, output_file):
    """
    Remove docstrings from a Python source file.

    This function reads the content of a Python file and parses it into an
    abstract syntax tree (AST). It then removes any docstrings found in function,
    class, asynchronous function, and module definitions by stripping the first
    expression in their bodies if it is a constant. If the source contains a
    syntax error, an error message is printed and processing is halted.
    The modified source code is written to the specified output file.
    """
    with open(input_file, "r", encoding="utf-8") as f:
        try:
            parsed = ast.parse(f.read())
        except SyntaxError as e:
            print(f"Skipping file {input_file} due to syntax error: {e}")
            return

    for node in ast.walk(parsed):
        if not isinstance(
            node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef, ast.Module)
        ):
            continue

        if not node.body:
            continue

        if not isinstance(node.body[0], ast.Expr):
            continue

        if not hasattr(node.body[0], "value") or not isinstance(
            node.body[0].value, ast.Constant
        ):
            continue

        node.body = node.body[1:]

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(astor.to_source(parsed))


def process_directory(input_dir, output_dir):
    """
    Recursively processes Python files in the input directory by removing their docstrings.

    Traverses the directory structure under input_dir, identifies files ending with ".py",
    and constructs corresponding output file paths in output_dir while preserving the original
    directory hierarchy. For each Python file, it creates any necessary output directories,
    removes the docstrings via remove_docstrings, and prints the processing status.

    Args:
        input_dir: Directory to search for Python files.
        output_dir: Base directory where processed files are saved.
    """
    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.endswith(".py"):  # Process only Python files (you can adjust this)
                input_file = os.path.join(root, file)
                relative_path = os.path.relpath(input_file, input_dir)
                output_file = os.path.join(output_dir, relative_path)

                output_dir_for_file = os.path.dirname(output_file)
                os.makedirs(output_dir_for_file, exist_ok=True)  # Create necessary dirs

                remove_docstrings(input_file, output_file)
                print(f"Processed: {input_file} -> {output_file}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python script.py <input_directory> <output_directory>")
        sys.exit(1)

    input_dir = sys.argv[1]
    output_dir = sys.argv[2]

    if not os.path.isdir(input_dir):
        print(f"Error: Input directory '{input_dir}' does not exist.")
        sys.exit(1)

    process_directory(input_dir, output_dir)
    print(f"Finished processing files in {input_dir}")
