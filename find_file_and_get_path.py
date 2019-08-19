import os


def find_file_and_get_path(dir_to_search, file_name_to_seach):
    """Use os.walk() find a file then return its path

    Use os.walk() to find a file, then get its file path and return the file path

    Args:
        dir_to_search: The directory to search in  
        file_name_to_seach: The file name to look for

    Returns:
        The file path

    Raises:
        None
    """
    for root, dirs, files in os.walk(dir_to_search):
        if file_name_to_seach in files:
            file_path = "%s/%s" % (root, file_name_to_seach)

    return file_path
