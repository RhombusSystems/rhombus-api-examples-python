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
