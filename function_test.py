"""
Gather and Count

Gather all the knob name in the script, once the knob names are gathered add them to a .txt
which is separated by a newline. A function is provided that will count how many times the name
is listed in the file.

Option is provided to clear out the txt files in a safe manner.
"""
from collections import defaultdict

import glob
import re
import os
import uuid


__SIGNATURE = "<scanline-test>"
__BASENAME_PATTERN = r"([\w-]+[\D])(\d+)?$"


def _mkdir(directory):
    """ Private function, make directory """
    try:
        os.mkdir(directory)
    except OSError:
        return False

    return True


def _validate_basename(dirname, basename):
    """
    If the basename exists then increment the basename.

    Args:
        dirname(str):       Directory path
        basename(str):      File basename

    Returns:
        (str) Incremented base name
    """
    # If the basename doesnt exist then we dont need to proceed to validate the version
    base_with_ext = os.path.splitext(basename)[0] + ".txt"

    if not filter(lambda f: f.lower() == base_with_ext.lower(), os.listdir(dirname)):
        return base_with_ext

    # Remove the .txt if applied, all if the user applies different ext
    basename = os.path.splitext(basename)[0]
    basename, increment = re.findall(pattern=__BASENAME_PATTERN, string=basename)[0]

    # Find if the files exist if so then increment version
    increment = int(increment or 0) + 1
    basename = "{}{}.txt".format(basename, increment)

    return _validate_basename(dirname, basename)


def clear_directory(directory, safe=False):
    """
    Check if all .txt extension files have the signature and remove
    the file, if safe, prompt to remove file before executions.

    Args:
        directory(str):     Path to directory

    Keyword Args:
        safe(bool):         Valid before remove, Default to False

    Returns:
        True if successful
    """
    # Find the txt files in the directory
    expr = os.path.join(directory, "*.txt")
    text_files = glob.glob(expr)

    for text in text_files:
        with open(text) as open_txt_file:
            if __SIGNATURE != open_txt_file.readline().strip():
                continue

        if safe:
            answer = raw_input("Would you like to delete {}? y".format(text))
            os.remove(text) if answer == "y" else None
        else:
            os.remove(text)

    return True


def find_all_knob_names(recursive=False):
    """
    Loop through all the nodes in the script and add their
    knob names into a list.

    Keyword Arg:
        recursive(bool):        Gather all nodes, defaults to False

    Yields:
        (iter) of knob names
    """
    # Gather all nodes inside root or if recursive is True gather nodes
    # inside groups nodes
    import nuke

    for node in nuke.allNodes(recurseGroups=recursive):
        for knob in node.allKnobs():
            name = knob.name()
            if not name:
                continue

            yield name


def knob_name_count(text):
    """
    Count the names in the text file, and return a dictionary with
    the key as the knob name and the number of times its presented
    in the text file.

    Args:
        text(str):      Path to file with

    Raises:
        OSError:        If the file doesnt exist

    Returns:
        (obj) Dictionary with key as name, and value of count
    """
    count = defaultdict(int)
    if not os.path.exists(text):
        raise OSError("Path doesn't exist, please provide a valid path.")

    # Gather the data and close the file object to avoid file lock.
    with open(text, "r") as open_text_file:
        open_text_file.seek(1)
        data = open_text_file.read().splitlines()

    for i, line in enumerate(data):
        # Skip the first line which is file verifier
        if i == 0:
            continue
        count[line] += 1

    return count


def write_to_text(names, dirname, basename=None):
    """
    Write the list to a text file, separated by a newline.

    Error:
        ValidateBaseName, ensure the filename isn't overriding existing

    Args:
        names(iter):         List of knob names
        dirname(str):        Location to store the file

    Keyword Args:
        basename(str):      Provide a basename, default to unique name.

    Returns:
        Text full file path
    """
    # Validate list of names
    if not names:
        raise ValueError("Please provide a list of node knob names")

    if basename:
        basename = _validate_basename(dirname, basename)
    else:
        basename = "{}.txt".format(str(uuid.uuid4()))

    # Check if the basename exist, else increment version.
    _mkdir(dirname)

    # In the case there are empty list items
    names = [__SIGNATURE] + [name for name in sorted(names) if name]
    names = "\n".join(names)
    text = os.path.join(dirname, basename)
    with open(text, "w") as open_text_file:
        open_text_file.write(names)

    return text


def test():
    """
    Providing a testing function, which will print the data required
    """
    dirname = os.getenv("HOME") or r"C:\Users\rober"
    dirname = os.path.join(dirname, "testing")

    names = ["testing"] * 1000000
    names = find_all_knob_names()
    text = write_to_text(names, dirname=dirname, basename="scanline-count.mov")

    for key, item in knob_name_count(text).iteritems():
        print key, item

    clear_directory(dirname, safe=False)


if __name__ == '__main__':
    test()









