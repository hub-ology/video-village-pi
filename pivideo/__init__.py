from __future__ import absolute_import
import logging
from pivideo.networking import get_hardware_address

logging.basicConfig(format='%(asctime)s	%(levelname)s:%(name)s:%(message)s', level=logging.INFO)

play_list = None
photo_overlay = None
encoder = None
PI_HARDWARE_ADDRESS = get_hardware_address('eth0')

import atexit
import collections
import contextlib
import datetime
import os
import requests
import schedule
import threading
import time
from urlparse import urlparse
from pivideo import omx
from pivideo.tasks import registration_task, fetch_show_schedule_task, setup_core_tasks
from pivideo.projector import Projector

FILE_CACHE = '/file_cache'

logger = logging.getLogger(__name__)

transcode_queue = collections.deque()

def cache_file(file_reference):
    """
    Locate a cached copy of a file.  If the file reference is not found in the
    cache and it's a network based resource, we'll fetch it and cache it and return
    a reference to the newly cached file.

    :returns: a string representing an absolute path to a local/cached copy of the file
    """
    url = urlparse(file_reference)
    if url.netloc:
        converted_filename = '{0}{1}'.format(url.netloc, url.path.replace('/', '-'))
        local_filename = os.path.join(FILE_CACHE, converted_filename)
        if not os.path.exists(local_filename):
            with contextlib.closing(requests.get(file_reference, stream=True)) as response:
                 with open(local_filename, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=1024):
                        if chunk:
                            f.write(chunk)
        return local_filename
    else:
        if os.path.exists(file_reference):
            return file_reference
        else:
            local_filename = os.path.join(FILE_CACHE, file_reference)
            return local_filename


def seconds_until_next_heartbeat():
    now = datetime.datetime.utcnow()
    return 60.0 - (now.second + (now.microsecond * 0.000001))


def heartbeat():
    global encoder
    global heartbeat_timer

    setup_core_tasks()

    while True:
        try:
            time.sleep(seconds_until_next_heartbeat())
            logger.debug('heartbeat')

            schedule.run_pending()

            if not encoder or not encoder.is_active():
                try:
                    video_info = transcode_queue.popleft()
                except IndexError:
                    pass
                else:
                    if encoder:
                        encoder.stop()
                    encoder = omx.Encoder(video_info.get('source_file'),
                                          video_info.get('target_file'),
                                          width=video_info.get('width'),
                                          height=video_info.get('height'))
        except:
            logger.exception('Error during heartbeat timer processing:')

heartbeat_thread = threading.Thread(target=heartbeat)
heartbeat_thread.daemon = True
heartbeat_thread.start()


def shutdown_handler():
    if encoder:
        encoder.stop()
    if photo_overlay:
        photo_overlay.stop()

atexit.register(shutdown_handler)


def current_status():

    encoder_status = {
        'active': encoder.is_active() if encoder else False,
        'queue': [item for item in transcode_queue]
    }

    play_list_active = play_list is not None and not play_list.stopped
    play_list_status = {
        'active': play_list_active,
        'audio': play_list.player.audio if play_list_active and play_list.player else {},
        'video': play_list.player.video if play_list_active and play_list.player else {},
        'mediafile': play_list.player.mediafile if play_list_active and play_list.player else None,
        'entries': play_list.entries if play_list_active else [],
        'loop': play_list.loop if play_list_active else False
    }

    overlay_active = photo_overlay.is_active() if photo_overlay else False
    overlay_status = {
        'active': overlay_active,
        'photo': photo_overlay.photo if photo_overlay else None,
        'layer': photo_overlay.layer if photo_overlay else None,
        'x': photo_overlay.x if photo_overlay else None,
        'y': photo_overlay.y if photo_overlay else None
    }

    projector_status = {
        "connected": False
    }

    try:
        with Projector() as p:
            projector_status['on'] = p.is_on()
            projector_status['connected'] = True
    except:
        logger.exception("Unable to determine current projector status.  Is it connected?")

    scheduled_jobs = [str(job) for job in schedule.jobs]

    tunnel_info = {}
    try:
        tunnels_response = requests.get('http://localhost:4040/api/tunnels')
        if tunnels_response.status_code == 200:
            tunnels = tunnels_response.json().get('tunnels', [])
            for tunnel in tunnels:
                tunnel_info[tunnel['name']] = tunnel.get('public_url')
    except:
        logger.exception('Unable to determine ngrok tunnel information')

    return {
        'hardware_address': PI_HARDWARE_ADDRESS,
        'scheduled_jobs': scheduled_jobs,
        'encoder': encoder_status,
        'play_list': play_list_status,
        'overlay': overlay_status,
        'projector': projector_status,
        'tunnels': tunnel_info
    }
