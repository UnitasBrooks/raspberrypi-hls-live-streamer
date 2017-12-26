from subprocess import call
from subprocess import Popen
from subprocess import PIPE
from os import remove
from os.path import basename

class Media(object):
    def __init__(self, media_file, ffmpeg="/usr/bin/ffmpeg", ffprobe="/usr/bin/ffprobe"):
        """
        Constructor

        :param media_file: media file to act on
        :param ffmpeg: path to ffmpeg
        :param ffprobe: path to ffprobe
        """
        self.media_file = media_file
        self.media_file_base_name = basename(media_file)
        self.ffmpeg = ffmpeg
        self.ffprobe = ffprobe

    def convert_to_ts(self, remove_original=True):
        """
        Converts the media file to a MPEG transport stream
        Example command: ffmpeg -i 5.h264 -an -vcodec copy -f mpegts 5.ts > /dev/null

        :param remove_original: removes the original file after copying.
        :return: ts file name
        """

        # New file will be the same as old but swap extension
        new_file = self.media_file.replace("h264", "ts")

        # Build the command array, pipe to dev null so we don't clutter the console.
        command = [self.ffmpeg, "-hide_banner", "-loglevel", "panic", "-i", self.media_file, "-an", "-vcodec", "copy",
                   "-f", "mpegts", new_file]

        # Run the command and check the exit code
        exit_code = call(command)
        if exit_code != 0:
            raise ConvertFailedError("Convert failed: " + " ".join(command))

        # clean up the
        if remove_original:
            remove(self.media_file)

        self.media_file = new_file
        self.media_file_base_name = basename(new_file)

        return self.media_file

    def get_duration(self):
        """
        Uses ffprobe to get the duration of the file duration

        :return: file duration
        """

        # Build ffprobe command
        command = self.ffprobe \
            + " -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 " \
            + self.media_file

        # Get duration
        duration = Popen(command, shell=True, stdout=PIPE).stdout.read()

        # Check that the duration is a float from ffprobe
        try:
            float(duration)
        except ValueError:
            raise DurationFetchError("Could not get duration, ffprobe output: " + duration)

        # Assuming \n line endings as this should be running on a raspberry pi
        return duration.rstrip("\n")


class ConvertFailedError(Exception):
    """
    Raised if we cannot convert a file from h264 to mpegts
    """
    pass


class DurationFetchError(Exception):
    """
    Raised if we cannot get the duration from ffprobe for our transport stream
    """
    pass
