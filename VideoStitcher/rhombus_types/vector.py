from typing import Union
import math as math

import numpy as np
from logging_utils.error import NumpyArrayError

def Vec2(x: float, y: float) -> np.ndarray:
    """Constructs a Vec2 numpy array

    :param x: The x value of the vector
    :param y: The y value of the vector
    :return: Returns the numpy array
    """

    return np.array([x, y])

def is_vec2(vector: np.ndarray) -> bool:
    """Checks to make sure that a numpy array is a Vec2

    :param vector: The numpy array to check
    :return: Returns whether the numpy array is a Vec2
    """
    if vector.shape != (2, ):
        return False
    if(vector.ndim != 1): 
        return False

    return True

def validate_vec2(vector: np.ndarray) -> None:
    """Checks to make sure that a numpy array is a Vec2 and if it isn't then throws an error

    :param vector: The numpy array to check
    """

    if not is_vec2(vector):
        raise NumpyArrayError("Not a Vec2!!", "Please make sure you are supplying a Vec2 to this function")

def vec2_len(a: np.ndarray) -> float:
    """Gets the length of a vector

    :param a: The vector
    :return: Returns the length of the vector
    """

    # Just the distance formula
    return math.sqrt(math.pow(a[0], 2) + math.pow(a[1], 2))

def vec2_compare(a: np.ndarray, b: Union[np.ndarray, float]):
    """Compares the length of vector a with either the length of vector b or a scalar

    :param a: The first vector
    :param b: The second vector or a scalar
    :return: Returns -1 if the length of a is greater than b, 1 if b is greater than a, and 0 if they are equal
    """

    if isinstance(b, float):
        if vec2_len(a) > b:
            return -1
        if vec2_len(a) < b:
            return 1
        return 0

    elif isinstance(b, np.ndarray):
        if vec2_len(a) > vec2_len(b):
            return -1
        if vec2_len(a) < vec2_len(b):
            return 1
        return 0

