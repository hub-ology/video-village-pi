import flask
from flask import Flask, request
import socket
import fcntl
import struct

import omx

player = None
encoder = None


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
@app.route("/play", methods=["POST"])
def play():
    global player
    if player:
        # stop playback if a video has already been started
        player.stop()

    video_file_name = request.json.get('video')
    player = omx.Player(video_file_name)

    return flask.jsonify(status='running', video=player.video, audio=player.audio)


@app.route("/transcode", methods=["POST"])
def transcode():
    global encoder
    if encoder:
        # stop encoding if a transcode task is still in progress
        encoder.stop()
    source_file = request.json.get('source_file')
    target_file = request.json.get('target_file')
    width = request.json.get('width', 800)
    height = request.json.get('height', 600)
    encoder = omx.Encoder(source_file, target_file,
                          width=width, height=height)
    return flask.jsonify(status='running')


@app.route("/status", methods=["GET"])
def status():
    global encoder, player
    return flask.jsonify(ip_address=get_ip_address('eth0'),
                         hardware_address=get_hardware_address('eth0'),
                         encoder_active=encoder.is_active() if encoder else False,
                         player_active=player.is_active() if player else False)

if __name__ == "__main__":
    app.run()
