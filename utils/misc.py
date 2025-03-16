import inspect
import os
import re
import sys
import unicodedata
from csv import DictWriter
from importlib import import_module
from io import StringIO


# ----------------------------------------------------------------------------------------------------
# * Import Classes
# ----------------------------------------------------------------------------------------------------
def import_classes(folder_name: str, class_type: type | None = None) -> list[type]:
    """
    Import and return all classes defined inside modules in the given folder and its subfolders.

    Args:
        folder_name: Path to the folder, relative to the working directory.
        class_type: If provided, only subclasses of this type are returned.

    Returns:
        List of imported class types.
    """
    classes = []

    # Resolve the absolute path and add the parent directory to sys.path
    base_path = os.path.join(os.getcwd(), folder_name)
    parent_dir = os.path.dirname(base_path)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

    if not os.path.exists(base_path) or not os.path.isdir(base_path):
        raise ValueError(
            f"Invalid folder: '{folder_name}' does not exist or is not a directory."
        )

    for root, _, files in os.walk(base_path):
        for file_name in files:
            if file_name.endswith(".py") and not file_name.startswith("__"):
                # Build module import path
                module_path = os.path.join(root, file_name)
                relative_module = os.path.relpath(module_path, parent_dir)
                module_name = relative_module.replace(os.sep, ".").removesuffix(".py")

                try:
                    module = import_module(module_name)
                except ModuleNotFoundError as e:
                    raise ModuleNotFoundError(
                        f"Import error: No module named '{module_name}'", e
                    )

                # Extract classes from the module
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    # Ensure the class is defined in the current module
                    if obj.__module__ == module_name:
                        if class_type is None or issubclass(obj, class_type):
                            classes.append(obj)

    return classes


# ----------------------------------------------------------------------------------------------------
# * Text Block
# ----------------------------------------------------------------------------------------------------
def text_block(text="") -> str:
    """Render given text as text block with border. This handle spaces, tabs, ANSI escape codes, and UTF-8 characters."""
    ansi_escape = re.compile(r"\x1b\[[0-9;]*[mG]")
    lines = text.splitlines()
    expanded_lines = [line.expandtabs() for line in lines]
    clean_lines = [ansi_escape.sub("", line) for line in expanded_lines]
    visual_lengths = [
        sum(1 + (unicodedata.east_asian_width(char) == "W") for char in line)
        for line in clean_lines
    ]
    max_len = max(visual_lengths) if visual_lengths else 0
    top_bottom_border = "┌" + "─" * (max_len + 2) + "┐"
    middle_lines = []
    for i, line in enumerate(expanded_lines):
        padding_needed = max_len - visual_lengths[i]
        padded_line = line + " " * padding_needed
        middle_lines.append(f"│ {padded_line} │")
    if not lines:
        middle_lines = ["│" + " " * (max_len + 2) + "│"]
    bottom_border = "└" + "─" * (max_len + 2) + "┘"
    return "\n".join([top_bottom_border] + middle_lines + [bottom_border])


# ----------------------------------------------------------------------------------------------------
# * Text Progress Bar
# ----------------------------------------------------------------------------------------------------
def text_progress_bar(
    current: float,
    max: float,
    length=5,
    filled_char="█",
    empty_char="░",
) -> str:
    """Render text progress bar using unicode characters."""
    normalized_value = min(int((current / (max or current or 1)) * length), length)
    return (normalized_value * filled_char) + ((length - normalized_value) * empty_char)


# ----------------------------------------------------------------------------------------------------
# * Clamp
# ----------------------------------------------------------------------------------------------------
def clamp(
    value: int | float, min_value: int | float, max_value: int | float
) -> int | float:
    """Constrain given value within specified range."""
    return max(min_value, min(value, max_value))


# ----------------------------------------------------------------------------------------------------
# * Number Sign
# ----------------------------------------------------------------------------------------------------
def numsign(value: int | float | str) -> str:
    """Format number with '+' or '-' sign prefix."""
    try:
        number = float(value)
    except ValueError:
        raise ValueError("Input must number or string representation of number.")
    if number.is_integer():
        number = int(number)
    return f"{'+' if number > 0 else ''}{number}"


# ----------------------------------------------------------------------------------------------------
# * Text CSV
# ----------------------------------------------------------------------------------------------------
def text_csv(data: dict | list[dict], replace_newline: str | None = None) -> str:
    """Convert given dictionary or dictionaries list to CSV string."""
    if not data:
        return ""
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        raise TypeError("Invalid input: not a dict or list.")
    if not all(isinstance(item, dict) for item in data):
        raise TypeError("Invalid input: not all items are dict.")
    fieldnames = data[0].keys()
    if not all(item.keys() == fieldnames for item in data):
        raise TypeError("Invalid input: dicts do not have same keys.")
    with StringIO() as output:
        writer = DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
        text = output.getvalue()
    return replace_newline.join(text.splitlines()) if replace_newline else text
