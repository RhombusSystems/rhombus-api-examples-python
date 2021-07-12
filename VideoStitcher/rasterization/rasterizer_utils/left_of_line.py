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
