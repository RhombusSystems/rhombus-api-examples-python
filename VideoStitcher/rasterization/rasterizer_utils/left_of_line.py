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

from rhombus_types.vector import Vec2, validate_vec2
import numpy as np

def left_of_line(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> bool:
    """Tests whether a point is to the left of a line.
    NOTE: Order of the points `a` and `b` matters. If you think of a line, the "left" changes based on where you start drawing the line. Keep this in mind when using this method. See the figure below!

    :param a: The first point of the line (starting from the "bottom" of the line).
    :param b: The second point of the line (starting from the "bottom" of the line).
    :param c: The point to test
    :return: Returns point `c` is to the left of the line ab

	                2
	                |
	                |
	     LEFT       |
	                |
	                |
	                1
	  
	  
	  
	                1
	                |
	                |
	                |       LEFT
	                |
	                |
	                2
    """

    validate_vec2(a)
    validate_vec2(b)
    validate_vec2(c)

    return ((b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])) > 0
