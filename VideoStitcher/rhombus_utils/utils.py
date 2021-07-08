import numpy as np

import math as math

from rhombus_utils.math import degrees_to_radians

from rhombus_types.vector import validate_vec2, Vec2

def geodetic_to_enu_simple_approximation(pos: np.ndarray, base: np.ndarray) -> np.ndarray:
    """Converts Latitude and Longitude to meters

    :param pos: The latitude longitude position to convert to a distance
    :param base: The latitude longitude position which `pos` will be compared to in meters
    :return: Returns an approximation in meters of how far `pos` is from `base`
    """

    # See https://stackoverflow.com/questions/17402723/function-that-converts-gps-coordinates-to-enu-coordinates for more info

    # Make sure we have Vec2 inputs
    validate_vec2(pos)
    validate_vec2(base)

    EARTH_MAJOR_AXIS: float = 6378137.0
    EARTH_FIRST_ECCENTRICITY_SQUARED: float = 0.00669437999014

    # Get the radians
    rad_lat = degrees_to_radians(pos[0])
    rad_lon = degrees_to_radians(pos[1])
    rad_base_lat = degrees_to_radians(base[0])
    rad_base_lon = degrees_to_radians(base[1])

    # Do the calculations
    dist_north = (EARTH_MAJOR_AXIS * (1 - EARTH_FIRST_ECCENTRICITY_SQUARED) / math.pow(1 - EARTH_FIRST_ECCENTRICITY_SQUARED * math.pow(math.sin(rad_base_lat), 2), 3.0 / 2)) * (rad_lat - rad_base_lat)

    dist_east = (EARTH_MAJOR_AXIS / math.sqrt(1 - EARTH_FIRST_ECCENTRICITY_SQUARED * math.pow(math.sin(rad_base_lat), 2))) * math.cos(rad_base_lat) * (rad_lon - rad_base_lon)

    # Return the result in meters
    return Vec2(dist_east, dist_north)


def feet_to_meters(feet: float) -> float:
    """Converts a distance in feet to distance in meters

    :param feet: The value in feet to convert
    :return: Returns the value in meters
    """
    return feet / 3.281
