"""
Main entry point to program, records video and uses hls_manifest and media modules to pass on h264 clips to create
our final stream.
"""
import picamera
import signal
import sys
from multiprocessing import Process
from media import Media
from hls_manifest import HLSManifest
import uuid
import time


class SecPi(object):
    def __init__(self, segment_length=5, width=640, height=480, debug=True):
        """
        Constructor

        :param segment_length: how long we should attempt to make our ts segments
        :param width: pixel width for capture resolution
        :param height: pixel height for capture resolution
        """
        self.segment_length = segment_length
        self.width = width
        self.height = height
        self.camera = picamera.PiCamera(resolution=(self.width, self.height))
        self.debug = debug

        # Initialize a manifest object with the attempted segment length, and a name
        self.manifest = HLSManifest(segment_length, uuid.uuid4().hex)

        # Set a signal handler for a user stopping the capture
        signal.signal(signal.SIGINT, self.signal_handler)

    def signal_handler(self, signal_caught, frame):
        """
        Clean up for when we exit

        :param signal_caught: needed for signal.signal()
        :param frame: needed for signal.signal()
        :return: None
        """
        self._debug("Stopping capture...")
        self.manifest.manifest_file.close()
        self.camera.stop_recording()
        sys.exit(0)

    def record(self):
        """
        Main capture loop for recording video
        :return: None
        """

        # Start camera and record initial segment
        self._debug("Starting camera...")
        self.camera.start_recording('video/1.h264')
        self.camera.wait_recording(self.segment_length)
        p = Process(target=self._process_segment, args=('video/1.h264',))
        p.start()
        i = 1

        while True:
            i += 1
            segment_location = 'video/' + str(i) + '.h264'
            self._debug("Created clip: " + segment_location)

            # Record a segment
            self.camera.split_recording(segment_location)
            self.camera.wait_recording(self.segment_length)

            # Process the segment asynchronously so we don't stop recording
            p = Process(target=self._process_segment, args=(segment_location,))
            p.start()

    def _process_segment(self, segment_location):
        # Convert Segment
        media = Media(segment_location)
        media.convert_to_ts()
        self._debug("Processed segment: " + media.media_file + ", Duration = " + media.get_duration())
        self.manifest.add_segment(media)

    def _debug(self, message):
        if self.debug:
            print(time.strftime("%Y-%m-%d %H:%M:%S") + " - " + message)


if __name__ == "__main__":
    # instantiate this camera object
    secpi = SecPi()
    secpi.record()

