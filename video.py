import flask
from flask import Flask
import socket
import fcntl
import struct

import pyomxplayer

player = None


def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15])
    )[20:24])


def get_hardware_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    info = fcntl.ioctl(s.fileno(), 0x8927,  struct.pack('256s', ifname[:15]))
    return ''.join(['%02x:' % ord(char) for char in info[18:24]])[:-1]


app = Flask(__name__)

#TODO: secure these routes such that only authorized clients may access
@app.route("/play", method="POST")
def play_video():
    global player
    if player:
        # stop playback if a video has already been started
        player.stop()

    video_file_name = ''
    player = pyomxplayer.OMXPlayer(video_file_name)

    return flask.jsonify(video=player.video, audio=player.audio)

@app.route("/status", method="GET")
def status():

    return flask.jsonify(ip=get_ip_address('eth0'))

if __name__ == "__main__":
    app.run()
