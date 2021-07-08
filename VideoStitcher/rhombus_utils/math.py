import math as math

def degrees_to_radians(degrees: float) -> float:
    """Converts degrees to radians
    
    :param degrees: The angle in degrees
    :return: Returns the radians result
    """
    return degrees * math.pi / 180

def normalize_angle(radians: float) -> float:
    """Isolates any radians angle to a radians angle between 0 and 2 PI
    
    :param radians: The angle in radians
    :return: Returns the same angle in radians, but ensures that it is between 0 and 2 PI
    """

    # While the radians is less than 0, we want to continually add 2 PI to it so that it will be within 0 and 2 PI
    while radians < 0:
        radians += 2 * math.pi

    # While the radians is greater than 2 PI, we want to continually subtract 2 PI to it so that it will be within 0 and 2 PI
    while radians > 2 * math.pi:
        radians -= 2 * math.pi

    return radians

def convert_rhombus_angle(radians: float) -> float:
    """Converts the Rhombus radians angle to our own coordinate space.
    The Rhombus API gives a rotation in radians, that increases clockwise and has 0 pointing North.
    We want to convert these angles to an angle where 0 is East, and it is rotating counter clockwise

    :param radians: The angle in radians that Rhombus gives
    :return: Returns the an equivalent angle in radians in our own coordinate space which is more similar to unit circle
    """

    # Rhombus Unit circle is going clockwise, we want it to go counter clockwise
    radians = -radians
    radians += 5 * math.pi / 2
    return normalize_angle(radians)
