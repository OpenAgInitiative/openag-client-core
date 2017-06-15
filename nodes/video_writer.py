#!/usr/bin/env python
"""
Stitches together the images from a recipe run and stores them as a video on
the recipe_start data point
"""
import os
import rospy
import tempfile
import threading
import subprocess

from couchdb import Server
from openag_lib.config import config as cli_config
from openag_lib.db_bootstrap.db_names import ENVIRONMENTAL_DATA_POINT
from openag_brain.video_helpers import *
from openag_brain.load_env_var_types import create_variables, VariableInfo

# Filter a list of environmental variables that are specific to camera
CAMERA_VARIABLES = create_variables(
    rospy.get_param('/var_types/camera_variables'))
RECIPE_START = VariableInfo.from_dict(
    rospy.get_param('/var_types/recipe_variables/recipe_start'))
RECIPE_END = VariableInfo.from_dict(
    rospy.get_param('/var_types/recipe_variables/recipe_end'))
IMAGE_ATTACHMENT = "image"
TIMELAPSE_ATTACHMENT = "timelapse"

IMAGE_FILENAME = "image.png"
WORKING_TIMELAPSE_FILENAME = "timelapse.mpeg"
TIMELAPSE_FILENAME = "timelapse.mp4"
SNIPPET_FILENAME = "snippet.mpeg"

# By default, each second of the timelapse will correspond to 1 day in real
# time
DEFAULT_TIMELAPSE_SCALING_FACTOR = 24*60*60

class VideoWriter(object):
    """
    Checks the environmental_variable_type for images posted for the given
    environment and variable over the course of a recipe run. It continuously
    builds a timelapse out of these images and saves it in the recipe_start
    data point for the recipe run.

    Timelapses are built up as MPEG-1 files because MPEG-1 supports file level
    concatenation. To add a new image to the end of the timelapse, a short
    video is created from that image and then appended to the growing
    timelapse. Then, the timelapse is converted to an mp4, which is easier for
    most video players to deal with.

    Conversion to mp4 is relatively expensive compared to the rest of the
    operations. If this becomes a performance issue, we could decrease the
    frequency with which this conversion is done. It's might be fine to only
    push an updated timelapse to the database once a day, for example.
    """
    def __init__(
            self, server, environment, variable, timelapse_scaling_factor
        ):
        # Save the parameters that were passed in
        self.data_db = server[ENVIRONMENTAL_DATA_POINT]
        self.environment = environment
        self.variable = variable
        self.timelapse_scaling_factor = timelapse_scaling_factor

        # Create a temporary directory to work in and pre-compute the full
        # paths for all of the files that we will be using
        self.working_dir = tempfile.mkdtemp()
        self.image_filepath = os.path.join(
            self.working_dir, IMAGE_FILENAME
        )
        self.working_timelapse_filepath = os.path.join(
            self.working_dir, WORKING_TIMELAPSE_FILENAME
        )
        self.timelapse_filepath = os.path.join(
            self.working_dir, TIMELAPSE_FILENAME
        )
        self.snippet_filepath = os.path.join(
            self.working_dir, SNIPPET_FILENAME
        )

        # These will be used to keep state about the recipe that is running (if
        # there is one)
        self.start_doc = None
        self.end_doc = None

        # Initialize change feeds
        self.last_seq_by_var = {}
        last_db_seq = self.data_db.changes(
            limit=1, descending=True
        )['last_seq']
        for var in [RECIPE_START, RECIPE_END, self.variable]:
            self.last_seq_by_var[var] = last_db_seq

        # Figure out when the most recent recipe started
        start_view = self.data_db.view("openag/by_variable", startkey=[
            self.environment, "desired", RECIPE_START.name
        ], endkey=[
            self.environment, "desired", RECIPE_START.name, {}
        ], group_level=3)
        if len(start_view) == 0:
            # No recipe has ever been run on this machine
            return
        self.start_doc = start_view.rows[0].value

        # Make sure the recipe hasn't ended yet
        end_view = self.data_db.view("openag/by_variable", startkey=[
            self.environment, "desired", RECIPE_END.name
        ], endkey=[
            self.environment, "desired", RECIPE_END.name, {}
        ], group_level=3)
        if len(end_view):
            self.end_doc = end_view.rows[0].value
            if (self.end_doc["timestamp"] > self.start_doc["timestamp"]):
                return

        # Download the current video and add any new frames to it
        # TODO: Check if any images were collected while this node was down and
        # add them to the video as well. This will be particularly important if
        # we decide to throttle posting the timelapse to the DB becasue that
        # would make it more likely for us to miss images
        self.init_video(self.start_doc)
        image_view = self.data_db.view("openag/by_variable", startkey=[
            self.environment, "measured", variable.name,
            self.start_doc["timestamp"]
        ], endkey=[
            self.environment, "measured", variable.name, {}
        ], group_level=4)
        for row in image_view:
            self.append_video(row.value)

    def __del__(self):
        import shutil
        shutil.rmtree(self.working_dir)

    def run(self):
        """
        We want to create 1 timelapse per video, so we wait for the recipe to
        start, process each new image, and then stop when the recipe stops
        """
        while True:
            rospy.sleep(5)
            if rospy.is_shutdown():
                break

            if self.start_doc and (not self.end_doc or self.start_doc["timestamp"] > self.end_doc["timestamp"]):
                # A recipe is running
                # Update the timelapse
                imgs = sorted(
                    self.get_variable_changes(self.variable),
                    key=lambda x: x["timestamp"]
                )
                for img in imgs:
                    self.append_video(img)
                # Check if the recipe has ended
                end_docs = self.get_variable_changes(RECIPE_END)
                if len(end_docs):
                    self.end_doc = max(end_docs, key=lambda x: x["timestamp"])
            else:
                # No recipe is running
                # Check if a recipe has started
                start_docs = self.get_variable_changes(RECIPE_START)
                if len(start_docs):
                    self.start_doc = max(start_docs, key=lambda x: x["timestamp"])
                    self.init_video(self.start_doc)

    def get_variable_changes(self, variable):
        """
        Get a list of all new environmental data points of the given variable
        since the last time this function was called with that variable
        """
        res = self.data_db.changes(
            since=self.last_seq_by_var.get(variable, 0),
            filter="openag/by_variable", variables=[variable],
            include_docs=True
        )
        self.last_seq_by_var[variable] = res["last_seq"]
        return [x["doc"] for x in res["results"]]

    def init_video(self, doc):
        """
        Takes a recipe_start data point for the current recipe and downloads
        the current timelape if there is one.
        """
        # Delte the old working timelapse if there is one
        if os.path.isfile(self.working_timelapse_filepath):
            os.remove(self.working_timelapse_filepath)

        # If we're in the middle of the recipe, download the current timelapse
        # from the DB so we can just append new images to it
        video = self.data_db.get_attachment(doc, TIMELAPSE_ATTACHMENT)
        if video is not None:
            with open(self.timelapse_filepath, "w+") as f:
                f.write(video.read())
            convert_video(
                self.timelapse_filepath, self.working_timelapse_filepath
            )

    def append_video(self, doc):
        """
        Takes a data point containing an image from the camera, appends it to
        the growing timelapse, and updates the timelapse file in the database.
        The duration that this frame appears in the timelapse is approximately
        proportional to the time between the previous image and this image
        """
        # Download the image
        image = self.data_db.get_attachment(doc, IMAGE_ATTACHMENT)
        if image is None:
            # We might see the document before the attachment is uploaded. Wait
            # a little while and try again
            rospy.sleep(1)
            image = self.data_db.get_attachment(doc, IMAGE_ATTACHMENT)
            if image is None:
                raise RuntimeError(
                    "Encountered an image data point with no image in it"
                )
        with open(self.image_filepath, "w+") as f:
            f.write(image.read())
            f.truncate()

        # Figure out how long the frame should last in the timelapse
        snippet_end_time = doc["timestamp"] - self.start_doc["timestamp"]
        snippet_end_time /= self.timelapse_scaling_factor
        if os.path.isfile(self.working_timelapse_filepath):
            current_video_duration = get_video_duration(
                self.working_timelapse_filepath
            )
        else:
            current_video_duration = 0
        snippet_duration = snippet_end_time - current_video_duration

        # If the snippet would last for less than a single frame of video,
        # there's no point in trying to add it
        if snippet_duration <= 0.04:
            return

        # Generate a video from the frame with the desired length
        create_video_from_image(
            self.image_filepath, self.snippet_filepath, snippet_duration
        )

        # Concatenate this video with the rest of the timelapse
        if os.path.isfile(self.timelapse_filepath):
            with open(self.snippet_filepath, "rb") as infile:
                with open(self.working_timelapse_filepath, "ab") as outfile:
                    outfile.write(infile.read())
        else:
            os.rename(self.snippet_filepath, self.working_timelapse_filepath)

        # Convert the working video to an mp4 and post it to the database
        convert_video(
            self.working_timelapse_filepath, self.timelapse_filepath
        )
        with open(self.timelapse_filepath, "r") as f:
            self.data_db.put_attachment(
                self.start_doc, f, TIMELAPSE_ATTACHMENT, "video/mp4"
            )

if __name__ == '__main__':
    db_server = cli_config["local_server"]["url"]
    if not db_server:
        raise RuntimeError("No local database specified")
    rospy.init_node("video_writer")
    try:
        timelapse_scaling_factor = rospy.get_param(
            "~timelapse_scaling_factor"
        )
    except KeyError:
        rospy.logwarn(
            "Timelapse scaling factor not specified. Defaulting to {}".format(
                DEFAULT_TIMELAPSE_SCALING_FACTOR
            )
        )
        timelapse_scaling_factor = DEFAULT_TIMELAPSE_SCALING_FACTOR
    server = Server(db_server)
    namespace = rospy.get_namespace()
    if namespace == '/':
        raise RuntimeError(
            "Video writer cannot be run in the global namespace. Please "
            "designate an environment for this module."
        )
    environment = namespace.split('/')[-2]
    for camera_var in CAMERA_VARIABLES.itervalues():
        mod = VideoWriter(
            server, environment, camera_var, timelapse_scaling_factor
        )
        threading.Thread(target=mod.run).start()
    rospy.spin()
