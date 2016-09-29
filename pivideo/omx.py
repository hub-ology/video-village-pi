# OpenMAX-based encoding and playback via Python
# Player based on https://github.com/jbaiter/pyomxplayer
import pexpect
import re
from collections import deque
import os
from threading import Thread
from time import sleep
import pivideo
import PIL
from PIL import ImageFont
from PIL import Image
from PIL import ImageDraw
import uuid


OVERLAY_TITLE_FONT = "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf"
OVERLAY_SUBTITLE_FONT = "/usr/share/fonts/truetype/freefont/FreeSerifItalic.ttf"
LOWER_THIRD_BACKGROUND = (17, 70, 153)


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


class PhotoOverlay(object):

    _LAUNCH_CMD = '/usr/local/bin/pngview -l {layer} {photofile} -x {x} -y {y}'

    def __init__(self, photofile=None, title='', subtitle='', layer=2, x=0, y=0,
                 finished_callback=None, duration=None):
        self.layer = layer
        self.x = x
        self.y = y
        self.finished_callback = finished_callback
        if duration is None:
            self.duration = 30
        else:
            self.duration = duration

        self.photo = photofile
        if self.photo is None:
            self.construct_lower_third_overlay(title, subtitle)
            if self.y == 0:
                self.y = 820

        cmd = self._LAUNCH_CMD.format(layer=layer, photofile=self.photo,
                                      x=self.x, y=self.y)
        self._process = pexpect.spawn(cmd)

        self._duration_thread = Thread(target=self.display_duration)
        self._duration_thread.start()

    def display_duration(self):
        sleep(self.duration)
        self.stop()
        if self.finished_callback:
            self.finished_callback()

    def construct_lower_third_overlay(self, title, subtitle):
        title_font = ImageFont.truetype(OVERLAY_TITLE_FONT ,150)
        sub_title_font = ImageFont.truetype(OVERLAY_TITLE_FONT ,72)
        img = Image.new("RGBA", (1920, 260), LOWER_THIRD_BACKGROUND)
        draw = ImageDraw.Draw(img)
        if title:
            draw.text((0, 0), title, (255, 255, 255), font=title_font)
        if subtitle:
            draw.text((0, 175), subtitle, (255, 255, 255), font=sub_title_font)
        draw = ImageDraw.Draw(img)
        self.photo = os.path.join(pivideo.FILE_CACHE, '{0}.png'.format(uuid.uuid1()))
        img.save(self.photo)

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
    _DURATION_REXP = re.compile(r".*Duration: (\s),.*")

    _LAUNCH_CMD = '/usr/bin/omxplayer -o both -s %s %s'
    _PAUSE_CMD = 'p'
    _TOGGLE_SUB_CMD = 's'
    _QUIT_CMD = 'q'
    _FASTER_CMD = '2'
    _SLOWER_CMD = '1'

    def __init__(self, mediafile, args=None, pause_playback=False,
                 finished_callback=None):
        if not args:
            args = ""
        cmd = self._LAUNCH_CMD % (mediafile, args)
        self._process = pexpect.spawn(cmd)
        self.paused = False
        self.subtitles_visible = True
        self.mediafile = mediafile
        self.video = {}
        self.audio = {}
        # Get video properties
        try:
            video_props = self._VIDEOPROP_REXP.match(self._process.readline()).groups()
            self.video['decoder'] = video_props[0]
            self.video['dimensions'] = tuple(int(x) for x in video_props[1:3])
            self.video['profile'] = int(video_props[3])
            self.video['fps'] = float(video_props[4])
        except AttributeError:
            pass
        # Get audio properties
        try:
            audio_props = self._AUDIOPROP_REXP.match(self._process.readline()).groups()
            self.audio['decoder'] = audio_props[0]
            (self.audio['channels'], self.audio['rate'],
             self.audio['bps']) = [int(x) for x in audio_props[1:]]
        except AttributeError:
            # this is due to entries with no audio
            pass

        self.finished = False
        self.finished_callback = finished_callback
        self.position = 0

        self._position_thread = Thread(target=self._get_position)
        self._position_thread.start()

        if pause_playback:
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
                self.stop()
                if self.finished_callback:
                    self.finished_callback()
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
        self.mediafile = None
        self.video = {}
        self.audio = {}
        self._process.send(self._QUIT_CMD)
        self._process.terminate(force=True)


class PlayList(object):

    def __init__(self, entries, loop=True):
        if entries is None:
            entries = []
        self.entries = entries
        self.queue = deque(entries)
        self.loop = loop
        self.player = None
        self.overlay = None
        self.stopped = True

    def cache_entries(self):
        """
            Cache entries referenced on the play list
        """
        for entry in self.entries:
            video_link = entry.get('video')
            if video_link:
                pivideo.cache_file(video_link)
            photo_link = entry.get('photo')
            if photo_link:
                pivideo.cache_file(photo_link)

    def next_entry(self):
        if not self.stopped:
            if self.loop:
                self.queue.rotate(-1)
            else:
                self.queue.popleft()
            self.play()

    def play(self):
        if len(self.queue) > 0:
            entry = self.queue[0]
            if 'video' in entry:
                if 'title' in entry:
                    subtitle = entry.get('subtitle', '')
                    self.overlay = PhotoOverlay(title=entry['title'],
                                                subtitle=subtitle, duration=10)
                video_file_name = pivideo.cache_file(entry['video'])
                self.player = Player(video_file_name, finished_callback=self.next_entry)
                self.stopped = False
            elif 'photo' in entry:
                photo_file_name = pivideo.cache_file(entry['photo'])
                duration = entry.get('duration', 60)
                self.overlay = PhotoOverlay(photofile=photo_file_name,
                                            duration=duration,
                                            finished_callback=self.next_entry)
                self.stopped = False
        else:
            self.stopped = True

    def stop(self):
        self.stopped = True
        if self.overlay:
            self.overlay.stop()
        if self.player:
            self.player.stop()


class Streamer(object):

    _LAUNCH_CMD = '/usr/local/bin/streamlink {} best -np "/usr/bin/omxplayer -o both" --yes-run-as-root'
    _QUIT_CMD = 'q'

    def __init__(self, stream_url, finished_callback=None):
        cmd = self._LAUNCH_CMD.format(stream_url)
        print(cmd)
        self._process = pexpect.spawn(cmd)
        self.stream_url = stream_url

        self.finished = False
        self.finished_callback = finished_callback

        self._monitor_thread = Thread(target=self._monitor_stream)
        self._monitor_thread.start()

    def _monitor_stream(self):
        self._process.expect(pexpect.EOF, timeout=None)
        self.finished = True
        self.stop()
        if self.finished_callback:
            self.finished_callback()

    def is_active(self):
        return self._process.isalive()

    def stop(self):
        self.stream_url = None
        self._process.send(self._QUIT_CMD)
        self._process.terminate(force=True)
