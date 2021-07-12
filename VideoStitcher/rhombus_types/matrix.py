import numpy as np
import math as math
from logging_utils.error import NumpyArrayError

def is_mat2(mat: np.ndarray) -> bool:
    """Checks to make sure that a numpy array is a Mat2

    :param mat: The numpy array to check
    :return: Returns whether the numpy array is a Mat2
    """
    if mat.shape != (2, 2):
        return False
    if(mat.ndim != 2): 
        return False

    return True

def validate_mat2(mat: np.ndarray) -> None:
    """Checks to make sure that a numpy array is a Mat2 and if it isn't then throws an error

    :param mat: The numpy array to check
    """

    if not is_mat2(mat):
        raise NumpyArrayError("Not a Mat2!!", "Please make sure you are supplying a Mat2 to this function")


def rotate(theta: float) -> np.ndarray:
    """Creates a 2x2 rotation matrix

    :param theta: The rotation this matrix will rotate by
    :return: Returns the resulting 2x2 rotation matrix
    """

    return np.array([[math.cos(theta), -math.sin(theta)], [math.sin(theta), math.cos(theta)]])
