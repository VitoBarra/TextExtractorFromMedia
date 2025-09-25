import  json
import os
import time


def WriteJson(path, json_object):
    with open(path, 'w') as f:
        json.dump(json_object, f, indent=4)


def ReadJson(path):
    with open(path, 'r') as f:
        return json.load(f)


def IsModifiedRecently(file_path, max_age_seconds):
    """
    Check if a file exists and was modified within the specified time frame.

    Args:
        file_path (str): Path to the file to check
        max_age_seconds (int): Maximum age in seconds to consider the file as fresh

    Returns:
        bool: True if file exists and was modified within max_age_seconds, False otherwise
    """
    if not os.path.exists(file_path):
        return False
    file_mtime = os.path.getmtime(file_path)
    return (time.time() - file_mtime) < max_age_seconds