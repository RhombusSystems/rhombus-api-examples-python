# Import OS and Shutils to get and delete a directory recursively
import os
import shutil


def cleanup(directory: str) -> None:
    """Deletes all files in a specified directory"""
    if os.path.isdir(directory):
        shutil.rmtree(directory)
