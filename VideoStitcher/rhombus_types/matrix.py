###################################################################################
# Copyright (c) 2021 Rhombus Systems                                              #
#                                                                                 # 
# Permission is hereby granted, free of charge, to any person obtaining a copy    #
# of this software and associated documentation files (the "Software"), to deal   #
# in the Software without restriction, including without limitation the rights    #
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell       #
# copies of the Software, and to permit persons to whom the Software is           #
# furnished to do so, subject to the following conditions:                        #
#                                                                                 # 
# The above copyright notice and this permission notice shall be included in all  #
# copies or substantial portions of the Software.                                 #
#                                                                                 # 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR      #
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,        #
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE     #
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER          #
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,   #
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE   #
# SOFTWARE.                                                                       #
###################################################################################

import numpy as np
import math
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
