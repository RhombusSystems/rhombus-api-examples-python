from typing import List, Set, Tuple, Union
import math

from rhombus_types.vector import Vec2
from rhombus_types.camera import Camera
from rhombus_services.graph_service import get_camera_plot, CameraPlot
from rhombus_types.events import ExitEvent
from rhombus_utils.velocity import normalize_velocity
from rasterization.triangle import Triangle, triangle_from_camera_plot, point_inside_triangle
from rasterization.canvas_size import get_canvas_size
from rasterization.trapezoid import new_capture_net, offset_capture_net, rotate_capture_net_from_velocity, point_inside_trapezoid

class Pixel:
    """A pixel is basically just an array of camera UUIDs which intersect with a pixel when rasterized. 

    :attribute cameras: The array of camera UUIDs which intersect with this pixel when rasterized.
    We store an array of camera UUIDs because we need to basically "alpha blend" the different cameras, to make sure that when camera's FOV's intersect, they will not be overwritten when rasterizing.
    This is why we can't store booleans, because we wouldn't have the necessary info of which cameras are where and values would get overwritten.
    """
    cameras: List[str]

    def __init__(self):
        """Constructor for a pixel"""

        self.cameras = list()

class Screen:
    """A screen is the result of rasterizing a list of cameras. It stores a 2D array of pixels so we know where each of the camera's viewports can see.

    :attribute pixels: 2D array of pixels which for this screen.
    :attribute meter_span: The canvas size in meters of all of the cameras.
    :attribute screen_size: The size in pixels of the square. This is determined from the `meterSpan` and the `pixelSize`.
    :attribute pixel_size: The size in meters of each of the pixels. This will be determined from the provided pixelsPerMeter value. If the pixelsPerMeter value is 10, then `pixelSize` is 1/10 of a meter.
    :attribute offset: The offset in meters that each of the camera's positions are. The Screen has an origin of the top left as (0, 0), whereas previously the origin was the originCamera.
    So in order to convert the camera space to screen space we need to offset all of the cameras by some amount in meters.
    """
    pixels: List[List[Pixel]]
    meter_span: float
    screen_size: int
    pixel_size: float
    offset: float

    def __init__(self, pixels: List[List[Pixel]], meter_span: float, screen_size: int, pixel_size: float, offset: float):
        """Constructor for a screen

        :param pixels: 2D array of pixels which for this screen.
        :param meter_span: The canvas size in meters of all of the cameras.
        :param screen_size: The size in pixels of the square. This is determined from the `meterSpan` and the `pixelSize`.
        :param pixel_size: The size in meters of each of the pixels. This will be determined from the provided pixelsPerMeter value. If the pixelsPerMeter value is 10, then `pixelSize` is 1/10 of a meter.
        :param offset: The offset in meters that each of the camera's positions are. The Screen has an origin of the top left as (0, 0), whereas previously the origin was the originCamera.
        So in order to convert the camera space to screen space we need to offset all of the cameras by some amount in meters.
        """

        self.pixels = pixels
        self.meter_span = meter_span
        self.screen_size = screen_size
        self.pixel_size = pixel_size
        self.offset = offset

class CaptureNetScreen:
    """This is a screen just for the capture net trapezoid which is a projection of a velocity. This is used to see which cameras are most likely to catch the person walking into the camera.

    :attribute pixels: In the capture net screen, we only need booleans instead of pixels since we are just checking whether a pixel is inside the capture net or not when rasterizing,
    there is no "alpha blending" in computer graphics terms.

    :attribute meter_span: The canvas size in meters of all of the cameras.
    :attribute screen_size: The size in pixels of the square. This is determined from the `meterSpan` and the `pixelSize`.
    :attribute pixel_size: The size in meters of each of the pixels. This will be determined from the provided pixelsPerMeter value. If the pixelsPerMeter value is 10, then `pixelSize` is 1/10 of a meter.
    """
    pixels: List[List[bool]]
    meter_span: float
    screen_size: int
    pixel_size: float

    def __init__(self, pixels: List[List[bool]], meter_span: float, screen_size: int, pixel_size: float):
        """Constructor for a screen

        :param pixels: In the capture net screen, we only need booleans instead of pixels since we are just checking whether a pixel is inside the capture net or not when rasterizing,
        there is no "alpha blending" in computer graphics terms.

        :param meter_span: The canvas size in meters of all of the cameras.
        :param screen_size: The size in pixels of the square. This is determined from the `meterSpan` and the `pixelSize`.
        :param pixel_size: The size in meters of each of the pixels. This will be determined from the provided pixelsPerMeter value. If the pixelsPerMeter value is 10, then `pixelSize` is 1/10 of a meter.
        """

        self.pixels = pixels
        self.meter_span = meter_span
        self.screen_size = screen_size
        self.pixel_size = pixel_size


def rasterize_cameras(cameras: List[CameraPlot], pixels_per_meter: float, meter_span: float) -> Screen:
    """Rasterizes an array of camera plots into a screen.

    :param cameras: The array of camera plots to rasterize
    :param pixels_per_meter: The number of pixels that should be rendered for each meter. This is essentially the density of pixels.
    :param meter_span: The size in meters of the canvas.
    :return: Returns the rasterized screen.
    """

    # Get the screen size in pixels.
    screen_size = math.ceil(pixels_per_meter * meter_span)

    # Get the pixel size in meters.
    pixel_size = 1 / pixels_per_meter

    # Get the offset by dividing the meter span by 2. This converts the origin (the center of the cameras) to the screen space origin (the top left of the screen).
    offset = meter_span / 2

    # Create our array of pixels.
    pixels: List[List[Pixel]] = list()

    # Loop through each of the cameras to rasterize each of them.
    for camera in cameras: 
        # We are going to create a triangle for the camera.
        triangle = triangle_from_camera_plot(camera, offset)

        # Loop through each of the pixels.
        for row in range (0, screen_size):
            for column in range(0, screen_size):
                # If the pixel row hasn't been initialized yet, then we will do that here.
                if pixels[row] == None:
                    pixels[row] = list()

                    # And we're just going to push empty pixels to this new array.
                    for _ in range(0, screen_size):
                        pixels[row].append(Pixel())

                # Next we are going to get the position of this pixel in world space.
                # We will simply multiply the x and y screen position by the pixel size in meters to get the position in world space.
                position = Vec2(column * pixel_size, row * pixel_size)

                # Now we will test whether the pixel is inside the triangle.
                inside = point_inside_triangle(triangle, position)

                # If it is inside...
                if inside:
                    # Then we will add whatever camera we are rendering to the pixel.
                    pixels[row][column].cameras.append(camera.uuid)


    return Screen(pixels=pixels, meter_span=meter_span, pixel_size=pixel_size, screen_size=screen_size, offset=offset)

def rasterize_velocity(exit_event: ExitEvent, capture_radius: float, screen: Screen) -> Tuple[CaptureNetScreen, Set[str]]:
    """Rasterizes a velocity capture net and determines which cameras were caught by this capture net.

    :param exit_event: The exit event to rasterize the velocity of.
    :param capture_radius: The capture radius of the net in meters.
    :param screen: The screen from rasterized cameras.
    :return: Returns the rasterized velocity screen for debugging purposes and a set of cameras.
    """

    # We are going to normalize the velocity of the exit event to prepare for rasterization.
    velocity = normalize_velocity(exit_event.velocity)

    # Create the capture net.
    capture_net = new_capture_net(capture_radius, screen.meter_span)

    # Rotate the capture net from the normalized velocity.
    rotated_capture_net = rotate_capture_net_from_velocity(capture_net, velocity)

    # Then translate the capture net by the screen offset in meters to transform the world space to screen space.
    net = offset_capture_net(rotated_capture_net, screen.offset)

    # Create our set of valid camera UUIDs
    valid_cameras: Set[str] = set()

    # Create the array of pixels for our capture net rasterization. We only need booleans for this since we are only really rasterizing one trapezoid and as such there is no "alpha blending".
    pixels: List[List[bool]] = list()

    # Loop through all fo the screen pixels
    for row in range(0, screen.screen_size):
        for column in range(0, screen.screen_size):
            # If the pixel row hasn't been initialized yet, then we will do that here.
            if pixels[row] == None:
                pixels[row] = list()

                # And we're just going to push false pixels to this new array.
                for _ in range(0, screen.screen_size):
                    pixels[row].append(False)

            # Next we are going to get the position of this pixel in world space.
            # We will simply multiply the x and y screen position by the pixel size in meters to get the position in world space.
            position = Vec2(column * screen.pixel_size, row * screen.pixel_size)

            # Now we will test whether the pixel is inside the triangle.
            inside = point_inside_trapezoid(net, position)

            # If it is inside...
            if inside:
                # Then we will set the pixel to true.
                pixels[row][column] = inside

                # And then add whatever cameras there are in the `screen` to our set of `validCameras`.
                for cam in screen.pixels[row][column].cameras:
                    valid_cameras.add(cam)

    # Then return our screen and valid cameras.
    return CaptureNetScreen(pixels=pixels, meter_span=screen.meter_span, screen_size=screen.screen_size, pixel_size=screen.pixel_size), valid_cameras


def get_valid_cameras(cameras: List[Camera], exit_event: ExitEvent, pixels_per_meter: float, capture_radius: float) -> List[Camera]:
    """Gets a list of valid cameras based on an exit event's velocity and the location of the cameras.
    
    :param cameras: The list of cameras that exist.
    :param exit_event: The exit event to look for cameras for.
    :param pixels_per_meter: The number of pixels that should be rendered for each meter. This is essentially the density of pixels.
    :param capture_radius: The capture radius of the net in meters.
    :return: Returns an array of valid cameras based on location of the cameras and the velocity of the exit event.
    """

    # Get the camera attached to the exit event
    origin = exit_event.events[0].camera

    # Only include cameras that don't match the origin UUID, since we will never "switch" to the same camera UUID.
    cameras = list(filter(lambda cam: cam.uuid != origin.uuid, cameras))

    # Next we will get the canvas size in meters.
    canvas_size = get_canvas_size(cameras, origin)
# And then plot all of the cameras we need.
    camera_plots = list(map(lambda cam: get_camera_plot(cam, origin), cameras))

    # Then we will rasterize the cameras.
    camera_screen = rasterize_cameras(camera_plots, pixels_per_meter, canvas_size[0])

    # And the velocity.
    _, result_cameras = rasterize_velocity(exit_event, capture_radius, camera_screen)

    # Create our array of valid cameras.
    valid_cameras: List[Camera] = list()

    # Loop through our resulting set of UUIDs and convert it to an array of cameras.
    for cam in result_cameras:
        for _cam in cameras:
            if _cam.uuid == cam:
                valid_cameras.append(_cam)

    # Return our cameras.
    return valid_cameras
