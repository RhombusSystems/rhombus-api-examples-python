# Import Subprocess to execute the ffmpeg command
import subprocess


def generate_frames(clip_path: str, directory_path: str, FPS: float = 1.0) -> None:
    """Generate frames at specified FPS using downloaded mp4 clip in the clip's same directory
    
    :param clip_path: The path of our clip.mp4 which we will use
    :param directory_path: The path where the clip.mp4 lies which is normally in res/<current time in seconds>
    :param FPS: Specifies how many frames to generate for our video, default 1.0
    """
    # All of the frame JPEGs will follow the naming scheme FRAME<index>.jpg where index starts at 1
    frame_name = "FRAME%4d.jpg"

    # Run the FFMpeg command, which looks something like ffmpeg -i res/<TIME_IN_SECONDS>/clip.mp4 -r 1.0 res/<TIME_IN_SECONDS>/FRAME%4d.jpg
    # where 1.0 is the FPS
    subprocess.run(["ffmpeg", "-i", clip_path, "-r", str(FPS), directory_path + frame_name], stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL)
