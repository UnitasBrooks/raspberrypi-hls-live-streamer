from math import floor
from time import sleep
"""
Module that handles creation of the HLS manifest, operates in a thread safe manner, so if processing of segments
finishes synchronously they will be written to the manifest in the correct order. This module also handles S3 upload
and file system / S3 segment retention.
"""

HEADER_TAGS = """#EXTM3U
#EXT-X-VERSION:3
#EXT-X-MEDIA-SEQUENCE:{{media_sequence}}
#EXT-X-TARGETDURATION:{{target_duration}}
"""
END_TAG = "#EXT-X-ENDLIST"
DURATION_TAG = "#EXTINF:{{duration}},"

SECONDS_IN_DAY = 86400


class HLSManifest(object):

    def __init__(self, target_segment_length, manifest_name, manifest_location="video/", manifest_keep_segments=None):

        self.target_segment_length = target_segment_length

        if manifest_keep_segments is None:
            self.manifest_keep_segments = self._get_segments_in_day()

        self.manifest_location = manifest_location
        self.manifest_keep_segments = manifest_keep_segments
        self.header = self._condition_header()
        self.segments_in_queue = []
        self.manifest_file = self._initialize_manifest(manifest_name)
        self.manifest_name = "video/" + manifest_name + ".m3u8"
        self.lock = False

    def add_segment(self, media):
        """
        Thread safe segment addition, sleeps while the lock is in place and then adds the first segment in the queue.
        :param media: Media object
        :return: None
        """
        self.segments_in_queue.append(media)
        while self.lock is True:
            sleep(.1)
        self._write_segment()

    def _initialize_manifest(self, manifest_name):
        """
        Creates a manifest file handler with a header.
        :param manifest_name: name of the manifest to create
        :return:
        """
        file_handle = open("video/" + manifest_name + ".m3u8", "a+")
        file_handle.write(self.header)
        file_handle.close()
        return file_handle

    def _write_segment(self):
        """
        Locks the manifest, writes to the first segment in the queue with duration tag and file name, then unlocks
        the manifest.
        :return: None
        """
        self.lock = True
        while len(self.segments_in_queue) > 0:
            media = self.segments_in_queue.pop(0)
            duration_tag = DURATION_TAG.replace("{{duration}}", media.get_duration())

            self.manifest_file = open(self.manifest_name, "a+")

            self.manifest_file.write(duration_tag + "\n")
            self.manifest_file.write(media.media_file_base_name + "\n")

            self.manifest_file.close()

        self.lock = False

    def _condition_header(self, media_sequence=0):
        """
        Creates a header string
        :param media_sequence: what sequence number we are starting at
        :return: the header
        """
        header = HEADER_TAGS.replace("{{media_sequence}}", str(media_sequence))
        header = header.replace("{{target_duration}}", str(self.target_segment_length + 1))
        return header

    def _get_segments_in_day(self):
        """
        Returns a days worth of segments
        :return:
        """
        return floor(SECONDS_IN_DAY / self.target_segment_length)
