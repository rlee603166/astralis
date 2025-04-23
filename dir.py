# backend/dir.py

import os

def pretty_print_directory(start_path='.', indent='', max_depth=None, depth=0, exclusions=None):
    """
    Recursively pretty print the directory structure starting from start_path.
    
    Parameters:
        start_path (str): The starting directory path (default: current directory).
        indent (str): Indentation string for the current level.
        max_depth (int): Maximum depth to traverse (None for unlimited).
        depth (int): Current depth level.
        exclusions (list): List of directory/file names to exclude.
    """
    if exclusions is None:
        exclusions = ['.git', '__pycache__', '.DS_Store', '.venv', 'venv', 'node_modules']
    
    if max_depth is not None and depth > max_depth:
        return
    
    # Print the current directory
    if depth == 0:
        print(os.path.basename(os.path.abspath(start_path)))
    
    # Get all items in the current directory
    try:
        items = sorted(os.listdir(start_path))
    except PermissionError:
        print(f"{indent}├── Permission denied")
        return
    
    # Filter out excluded items
    items = [item for item in items if item not in exclusions]
    
    # Process each item
    for i, item in enumerate(items):
        path = os.path.join(start_path, item)
        is_last = (i == len(items) - 1)
        
        # Use different symbols for the last item
        if is_last:
            print(f"{indent}└── {item}")
            next_indent = indent + "    "
        else:
            print(f"{indent}├── {item}")
            next_indent = indent + "│   "
        
        # Recursively process subdirectories
        if os.path.isdir(path):
            pretty_print_directory(path, next_indent, max_depth, depth + 1, exclusions)

# Example usage:
pretty_print_directory('/Users/andrewyang/git/deep-linked/backend', max_depth=4)
