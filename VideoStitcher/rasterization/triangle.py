import numpy as np
from rhombus_types.vector import Vec2, validate_vec2
from rhombus_services.graph_service import CameraPlot
from rasterization.rasterizer_utils.left_of_line import left_of_line

class Triangle:
    """A triangle is used during rasterization as a simple primitive. NOTE: The points p0, p1, and p2 must be set counter clockwise, otherwise linetests will be wrong.

    :attribute p0: The X Y position of vertex 0 in the triangle.
    :attribute p1: The X Y position of vertex 1 in the triangle.
    :attribute p2: The X Y position of vertex 2 in the triangle.
    """

    p0: np.ndarray
    p1: np.ndarray
    p2: np.ndarray

    def __init__(self, p0: np.ndarray, p1: np.ndarray, p2: np.ndarray): 
        """Constructor for a Triangle

        :param p0: The X Y position of vertex 0 in the triangle.
        :param p1: The X Y position of vertex 1 in the triangle.
        :param p2: The X Y position of vertex 2 in the triangle.
        """
        validate_vec2(p0)
        validate_vec2(p1)
        validate_vec2(p2)

        self.p0 = p0
        self.p1 = p1
        self.p2 = p2

def triangle_from_camera_plot(camera: CameraPlot, offset: float) -> Triangle:
    """Converts a CameraPlot (which creates a triangle with 3 vertices) into a Triangle interface which the rasterizer can use.

    :param camera: The CameraPlot to be transformed into a rasterizable triangle.
    :param offset: Because the coordinate space of the CameraPlot has the origin camera as (0, 0), the offset is used to convert the vertices in this coordinate space 
    to screenspace where (0, 0) is the top left of the screen.

    :return: Returns the triangle that the CameraPlot was transformed into.
    """

    return Triangle(
                p0=Vec2(camera.x[0] + offset, camera.y[0] + offset),
                p1=Vec2(camera.x[1] + offset, camera.y[1] + offset),
                p2=Vec2(camera.x[2] + offset, camera.y[2] + offset)
            )


def point_inside_triangle(triangle: Triangle, point: np.ndarray) -> bool:
    """Tests whether a X Y position is inside of a triangle or not
    
    :param triangle: The triangle to test the point inside.
    :param point: The point we are testing.
    :return: Returns true if the point is inside of the triangle.
    """

    # We know that the triangle's points are going counter clockwise, so we are just going to test that `point` is to the left of each of the lines and if it is then we know `point` is inside of `triangle`.
    l1 = left_of_line(triangle.p0, triangle.p1, point)
    l2 = left_of_line(triangle.p1, triangle.p2, point)
    l3 = left_of_line(triangle.p2, triangle.p0, point)
    return l1 and l2 and l3
