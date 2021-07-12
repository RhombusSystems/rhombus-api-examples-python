import numpy as np
import math
from rhombus_types.vector import Vec2
from rhombus_types.matrix import rotate, apply
from rasterization.rasterizer_utils.left_of_line import left_of_line
from logging_utils.error import NonNormalizedVectorError

class CaptureNetTrapezoid:
    """Primitive trapezoid which is used to project a velocity to see which camera's FOV's intersect. 
    NOTE: The points p0, p1, p2, and p3 must be set counter clockwise, otherwise linetests will be wrong.

    :attribute p0: The X Y position of vertex 0 in the triangle.
    :attribute p1: The X Y position of vertex 1 in the triangle.
    :attribute p2: The X Y position of vertex 2 in the triangle.
    :attribute p3: The X Y position of vertex 3 in the triangle.
    """
    p0: np.ndarray
    p1: np.ndarray
    p2: np.ndarray
    p3: np.ndarray

    def __init__(self, p0: np.ndarray, p1: np.ndarray, p2: np.ndarray, p3: np.ndarray):
        """Constructor for the a capture net trapezoid

        :param p0: The X Y position of vertex 0 in the triangle.
        :param p1: The X Y position of vertex 1 in the triangle.
        :param p2: The X Y position of vertex 2 in the triangle.
        :param p3: The X Y position of vertex 3 in the triangle.
        """

        self.p0 = p0
        self.p1 = p1
        self.p2 = p2
        self.p3 = p3

def new_capture_net(capture_radius: float, meter_span: float):
    """Creates a capture net based on a specified radius and meterSpan. This trapezoid will not be transformed properly into worldspace, but it will be a basic primitive that will later be rotated properly.
    
    :param capture_radius: The capture radius specifies the size in meters of the large side of the trapezoid (pointing out from the center). 
    The larger this value, the more cameras will be "captured" within this "net"

    :param meter_span: The canvas size in meters of all of the cameras.
    This is used because this will be the length of the capture net so that even cameras on the very edge of the screen can still be caught.

    :return: A trapezoid with the specified capture Radius and meter span pointing left from the origin that hasn't been rotated or transformed.
    """

    return CaptureNetTrapezoid(
                p0=Vec2(meter_span, -0.5 - (capture_radius - 1) / 2),
                p1=Vec2(meter_span, 0.5 + (capture_radius - 1) / 2),
                p2=Vec2(0, 0.5),
                p3=Vec2(0, -0.5)
            )

def offset_capture_net(capture_net: CaptureNetTrapezoid, offset: float) -> CaptureNetTrapezoid:
    """Translates a capture net by a specified offset.

    :param capture_net: The capture net to translate.
    :param offset: The amount in meters to translate the capture net. This is just a number instead of a Vec2 since we are only dealing with squares.
    :return: The resulting capture net after the transformation.
    """

    return CaptureNetTrapezoid(
                p0=Vec2(capture_net.p0[0] + offset, capture_net.p0[1] + offset),
                p1=Vec2(capture_net.p1[0] + offset, capture_net.p1[1] + offset),
                p2=Vec2(capture_net.p2[0] + offset, capture_net.p2[1] + offset),
                p3=Vec2(capture_net.p3[0] + offset, capture_net.p3[1] + offset),
            )

def rotate_capture_net_from_velocity(capture_net: CaptureNetTrapezoid, velocity: np.ndarray) -> CaptureNetTrapezoid:
    """Rotates a capture net using a normalized velocity.
    Since there is no good way to know the exact direction someone may have walked of screen, we use general angles using a normalized velocity to see where the use _probably_ walked off.

    :param capture_net: The capture net to translate.
    :param velocity: The NORMALIZED velocity of the human. The HAS to be normalized, otherwise this method won't work.
    :return: The resulting capture net after the rotation.
    """

    # The rotation we need to rotate the capture net by in radians.
    rotation: float = 0


	# If the velocity is 0, then we can't do anything and there shouldn't be an exit event at all.
	# 
	# The normalized velocity on the X axis has a value of 1 be right on the unit circle, and -1 be left.
	# The normalized velocity on the Y axis has a value of 1 be bottom on the unit circle, and -1 be top.
    if velocity[0] == 0 and velocity[1] == 0:
        raise NonNormalizedVectorError("No Velocity!", "Provided normalized velocity is 0")
    elif velocity[0] == 1 and velocity[1]== 0:
        return capture_net
    elif velocity[0] == 1 and velocity[1] == 1: 
        rotation = -math.pi / 4;
    elif velocity[0] == 1 and velocity[1] == -1: 
        rotation = math.pi / 4;
    elif velocity[0] == -1 and velocity[1] == 0: 
        rotation = math.pi;
    elif velocity[0] == -1 and velocity[1] == 1: 
        rotation = -3 * math.pi / 4;
    elif velocity[0] == -1 and velocity[1] == -1: 
        rotation = -5 * math.pi / 4;
    elif velocity[0] == 0 and velocity[1] == 1: 
        rotation = -math.pi / 2;
    elif velocity[0] == 0 and velocity[1] == -1: 
        rotation = math.pi / 2;
    else: 
        raise NonNormalizedVectorError("Non normalized velocity provided!", "Please make sure that you are using a normalized velocity!")

    # We are going to create a 2x2 rotation matrix using our `rotation`.
    rotation_matrix = rotate(rotation)

    # And then rotate all of the capture net's vertices.
    p0 = rotation_matrix.dot(capture_net.p0)
    p1 = rotation_matrix.dot(capture_net.p1)
    p2 = rotation_matrix.dot(capture_net.p2)
    p3 = rotation_matrix.dot(capture_net.p3)

    # Then return the new trapezoid
    return CaptureNetTrapezoid(
            p0=p0,
            p1=p1,
            p2=p2,
            p3=p3,
            )

def point_inside_trapezoid(trapezoid: CaptureNetTrapezoid, point: np.ndarray) -> bool:
    """Tests whether a X Y position is inside of a triangle or not

    :param trapezoid: The trapezoid to test the point inside.
    :param point: The point we are testing.
    :return: The resulting capture net after the transformation.
    """

    # We know that the trapezoid's points are going counter clockwise, so we are just going to test that `point` is to the left of each of the lines and if it is then we know `point` is inside of `trapezoid`.
    l1 = left_of_line(trapezoid.p0, trapezoid.p1, trapezoid.p2)
    l2 = left_of_line(trapezoid.p1, trapezoid.p2, trapezoid.p2)
    l3 = left_of_line(trapezoid.p2, trapezoid.p3, trapezoid.p2)
    l4 = left_of_line(trapezoid.p3, trapezoid.p0, trapezoid.p2)

    return l1 and l2 and l3 and l4
