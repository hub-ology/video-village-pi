from __future__ import absolute_import
import logging
import flask
from flask import Flask, request
import schedule

import pivideo
from pivideo.networking import get_ip_address, get_hardware_address
from pivideo import encoder, transcode_queue, photo_overlay, play_list
from pivideo import omx
from pivideo.projector import Projector
from pivideo.tasks import schedule_show

logger = logging.getLogger(__name__)

app = Flask(__name__)


@app.route("/overlay", methods=["POST"])
def overlay():
    global photo_overlay

    # stop displaying the current photo if there's an active overlay
    if photo_overlay:
        photo_overlay.stop()

    photo = request.json.get('photo')
    title = request.json.get('title')
    x = request.json.get('x', 0)
    y = request.json.get('y', 0)

    if photo:
        photo_file_name = pivideo.cache_file(photo)
        photo_overlay = omx.PhotoOverlay(photo_file_name, x=x, y=y)
        return flask.jsonify(status='active')
    elif title:
        subtitle = request.json.get('subtitle')
        photo_overlay = omx.PhotoOverlay(title=title, subtitle=subtitle, x=x, y=y)
        return flask.jsonify(status='active')
    else:
        return flask.jsonify(status='stopped')

def playback_finished():
    logger.info('playback finished!')

@app.route("/play", methods=["POST"])
def play():
    global play_list
    # stop playback if active
    if play_list:
        play_list.stop()

    video = request.json.get('video')
    if video:
        play_list_videos = [request.json]
    else:
        play_list_videos = request.json.get('play_list')

    if play_list_videos:
        loop = request.json.get('loop', False)
        start_time = request.json.get('start_time')
        end_time = request.json.get('end_time')
        if start_time and end_time:
            schedule_show(start_time, end_time, play_list_videos, loop=loop)
            return flask.jsonify(status='scheduled')
        else:
            play_list = omx.PlayList(play_list_videos, loop=loop)
            play_list.play()
            return flask.jsonify(status='running')
    else:
        return flask.jsonify(status='stopped')


@app.route("/projector/on", methods=["POST"])
def projector_on():
    success = False
    try:
        with Projector() as p:
            success = p.power_on()
    except:
        logger.exception('Unable to turn on projector.  Is it connected?')

    return flask.jsonify(status=success)


@app.route("/projector/off", methods=["POST"])
def projector_off():
    success = False
    try:
        with Projector() as p:
            success = p.power_off()
    except:
        logger.exception('Unable to turn off projector.  Is it connected?')

    return flask.jsonify(status=success)


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
    status_info = pivideo.current_status()
    return flask.jsonify(status_info)
