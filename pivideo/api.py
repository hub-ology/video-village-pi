import flask
from flask import Flask, request

import pivideo
from pivideo import get_ip_address, get_hardware_address
from pivideo import player, encoder, transcode_queue, photo_overlay
from pivideo import omx


app = Flask(__name__)

#TODO: secure these routes such that only authorized clients may access


@app.route("/overlay", methods=["POST"])
def overlay():
    global photo_overlay

    # stop displaying the current photo if there's an active overlay
    if photo_overlay:
        photo_overlay.stop()

    photo = request.json.get('photo')
    if photo:
        photo_file_name = pivideo.cache_file(photo)
        x = request.json.get('x', 0)
        y = request.json.get('y', 0)
        photo_overlay = omx.PhotoOverlay(photo_file_name, x=x, y=y)
        return flask.jsonify(status='active')
    else:
        return flask.jsonify(status='stopped')

@app.route("/play", methods=["POST"])
def play():
    global player
    if player:
        # stop playback if a video has already been started
        player.stop()

    video = request.json.get('video')
    if video:
        video_file_name = pivideo.cache_file(video)
        player = omx.Player(video_file_name)
        return flask.jsonify(status='running', video=player.video, audio=player.audio)
    else:
        return flask.jsonify(status='stopped')


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

    encoder_status = {
        'active': encoder.is_active() if encoder else False,
        'queue': [item for item in transcode_queue]
    }
    player_active = player.is_active() if player else False
    player_status = {
        'active': player_active,
        'audio': player.audio if player_active else {},
        'video': player.video if player_active else {},
        'mediafile': player.mediafile if player_active else None
    }
    overlay_active = photo_overlay.is_active() if photo_overlay else False
    overlay_status = {
        'active': overlay_active,
        'photo': photo_overlay.photo if photo_overlay else None,
        'layer': photo_overlay.layer if photo_overlay else None,
        'x': photo_overlay.x if photo_overlay else None,
        'y': photo_overlay.y if photo_overlay else None
    }

    return flask.jsonify(hardware_address=get_hardware_address('eth0'),
                         encoder=encoder_status,
                         player=player_status,
                         overlay=overlay_status)
