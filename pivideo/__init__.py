from __future__ import absolute_import
import logging

logging.basicConfig(format='%(asctime)s	%(levelname)s:%(name)s:%(message)s', level=logging.INFO)

play_list = None
photo_overlay = None
encoder = None

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
