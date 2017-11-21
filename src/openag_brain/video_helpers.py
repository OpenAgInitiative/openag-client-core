"""
A set of helper functions that operate on videos. They all use subprocess to
wrap ffmpeg commands to abstract the syntax
"""
import subprocess

__all__ = ["convert_video", "get_video_duration", "create_video_from_image"]

def convert_video(in_path, out_path):
    """
    Converts the video at `in_path` into the format implied by `out_path` and
    writes it to `out_path`
    """
    if subprocess.call([
        "avconv", "-y", "-i", in_path, out_path
    ]):
        raise RuntimeError(
            'Failed to convert file "{}" to "{}"'.format(in_path, out_path)
        )

def get_video_duration(path):
    """
    Returns the duration of the video file at `path` in seconds
    """
    res = subprocess.check_output([
        "avprobe", "-i", path, "-show_entries", "format=duration"
    ])

    # The output of ffprobe with the parameters should be as follows:
    # [FORMAT]
    #     duration=???
    # [/FORMAT]
    # This line of code extracts the word "duration" and the value from this
    # string
    [k, v] = res.split()[1].split('=')
    if k != "duration":
        raise RuntimeError("Failed to get video duration")
    return float(v)

def create_video_from_image(image_path, video_path, duration):
    """
    Creates a video of the requested duration in which every frame is the still
    image at `image_path` and stores the result at `video_path`
    """
    if subprocess.call([
        "avconv", "-y", "-loop", "1", "-i", image_path, "-t",
        str(duration), "-pix_fmt", "yuv420p", video_path
    ]):
        raise RuntimeError("Failed to generate video from image")
