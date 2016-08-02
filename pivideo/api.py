import flask
from flask import Flask, request

from pivideo import get_ip_address, get_hardware_address
from pivideo import player, encoder, transcode_queue
from pivideo import omx


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
    video_info = {
        'source_file': request.json.get('source_file'),
        'target_file': request.json.get('target_file'),
        'width': request.json.get('width', 800),
        'height': request.json.get('height', 600)
    }
    transcode_queue.append(video_info)
    return flask.jsonify(status='queued')


@app.route("/status", methods=["GET"])
def status():
    global encoder, player
    return flask.jsonify(hardware_address=get_hardware_address('eth0'),
                         encoder_active=encoder.is_active() if encoder else False,
                         player_active=player.is_active() if player else False,
                         transcode_queue=[item for item in transcode_queue])
