# OpenMAX-based encoding and playback via Python
# Player based on https://github.com/jbaiter/pyomxplayer
import pexpect
import re

from threading import Thread
from time import sleep

class Encoder(object):

    _LAUNCH_CMD = ('/usr/bin/gst-launch-1.0 filesrc location={source_file} ! '
                   'decodebin ! videoconvert ! videoscale ! '
                   'video/x-raw,width={width},height={height} ! '
                   'omxh264enc ! h264parse ! mp4mux ! '
                   'filesink location={target_file}')

    def __init__(self, source_file, target_file, width=800, height=600):
        cmd = self._LAUNCH_CMD.format(source_file=source_file,
                                      target_file=target_file,
                                      width=800,
                                      height=600)

        self._process = pexpect.spawn(cmd)

    def is_active(self):
        return self._process.isalive()

    def stop(self):
        self._process.sendcontrol('c')
        self._process.terminate(force=True)


class Player(object):

    _FILEPROP_REXP = re.compile(r".*audio streams (\d+) video streams (\d+) chapters (\d+) subtitles (\d+).*")
    _VIDEOPROP_REXP = re.compile(r".*Video codec ([\w-]+) width (\d+) height (\d+) profile (-?\d+) fps ([\d.]+).*")
    _AUDIOPROP_REXP = re.compile(r"Audio codec (\w+) channels (\d+) samplerate (\d+) bitspersample (\d+).*")
    _STATUS_REXP = re.compile(r"M:\s*(\d+).*")
    _DONE_REXP = re.compile(r"have a nice day.*")

    _LAUNCH_CMD = '/usr/bin/omxplayer -s %s %s'
    _PAUSE_CMD = 'p'
    _TOGGLE_SUB_CMD = 's'
    _QUIT_CMD = 'q'
    _FASTER_CMD = '2'
    _SLOWER_CMD = '1'

    paused = False
    subtitles_visible = True

    def __init__(self, mediafile, args=None, start_playback=False):
        if not args:
            args = ""
        cmd = self._LAUNCH_CMD % (mediafile, args)
        self._process = pexpect.spawn(cmd)

        self.video = dict()
        self.audio = dict()
        # Get video properties
        video_props = self._VIDEOPROP_REXP.match(self._process.readline()).groups()
        self.video['decoder'] = video_props[0]
        self.video['dimensions'] = tuple(int(x) for x in video_props[1:3])
        self.video['profile'] = int(video_props[3])
        self.video['fps'] = float(video_props[4])
        # Get audio properties
        try:
            audio_props = self._AUDIOPROP_REXP.match(self._process.readline()).groups()
            self.audio['decoder'] = audio_props[0]
            (self.audio['channels'], self.audio['rate'],
             self.audio['bps']) = [int(x) for x in audio_props[1:]]
        except AttributeError:
            # this is due to videos with no audio
            pass

        self.finished = False
        self.position = 0

        self._position_thread = Thread(target=self._get_position)
        self._position_thread.start()

        if start_playback:
            self.toggle_pause()
        self.toggle_subtitles()

    def _get_position(self):
        while True:
            index = self._process.expect([self._STATUS_REXP,
                                            pexpect.TIMEOUT,
                                            pexpect.EOF,
                                            self._DONE_REXP])
            if index == 1: continue
            elif index in (2, 3):
                self.finished = True
                break
            else:
                self.position = float(self._process.match.group(1))
            sleep(0.05)

    def is_active(self):
        return self._process.isalive()

    def toggle_pause(self):
        if self._process.send(self._PAUSE_CMD):
            self.paused = not self.paused

    def toggle_subtitles(self):
        if self._process.send(self._TOGGLE_SUB_CMD):
            self.subtitles_visible = not self.subtitles_visible

    def stop(self):
        self._process.send(self._QUIT_CMD)
        self._process.terminate(force=True)
