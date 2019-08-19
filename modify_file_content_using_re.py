import os
import re


def modify_file_content_using_re(file, old_str, new_str):
    """Use re.sub() to modify file content

    Read file, then use re.sub() to read every line, check if specified string exists, if yes, replace it with a given string.

    Args:
        file: The file path
        old_str: The string to search to be replaced
        new_str: The string to replace with

    Returns:
        None

    Raises:
        None
    """
    with open(file, "r", encoding="utf-8") as f1, open("%s.back" % file, "w", encoding="utf-8") as f2:
        for line in f1:
            f2.write(re.sub(old_str, new_str, line))
    os.remove(file)
    os.rename("%s.back" % file, file)
