from __future__ import absolute_import
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
import logging
from pivideo.networking import get_hardware_address, get_ip_address

logging.basicConfig(format='%(asctime)s	%(levelname)s:%(name)s:%(message)s', level=logging.INFO)

version = 'v0.5'

play_list = None
photo_overlay = None
encoder = None
transcode_queue = collections.deque()
PI_HARDWARE_ADDRESS = get_hardware_address('eth0')
PI_IP_ADDRESS = get_ip_address('eth0')

from pivideo import omx
from pivideo.tasks import setup_core_tasks, registration_task, report_pi_status_task, fetch_show_schedule_task
from pivideo.projector import Projector
from gpiozero import CPUTemperature

FILE_CACHE = '/file_cache'

logger = logging.getLogger(__name__)

try:
    cpu_temp = CPUTemperature()
except IOError:
    cpu_temp = None


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
    global photo_overlay
    global play_list
    global heartbeat_timer

    setup_core_tasks()
    # run some of the configured core tasks immediately on start up
    # and then on the normal schedule afterward
    registration_task()
    fetch_show_schedule_task()
    report_pi_status_task()


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


def bytes2human(n):
    symbols = ('K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')
    prefix = {}
    for i, s in enumerate(symbols):
        prefix[s] = 1 << (i+1)*10
    for s in reversed(symbols):
        if n >= prefix[s]:
            value = float(n) / prefix[s]
            return '{0:.1f}{1}'.format(value, s)
    return "{0}B".format(n)


def file_cache_size():
    """
        Reports size of FILE_CACHE directory
    """
    try:
        cached_byte_count = 0
        for cached_file_name in os.listdir(FILE_CACHE):
            cached_file_path = os.path.join(FILE_CACHE, cached_file_name)
            if os.path.isfile(cached_file_path):
                cached_byte_count += os.path.getsize(cached_file_path)

        return bytes2human(cached_byte_count)
    except:
        logger.exception('Unable to determine file cache size')
        return 'unknown'


def disk_usage(path="/"):
    """
        Gather disk usage information for the specified path
    """
    human_available = 'unknown'
    human_capacity = 'unknown'
    human_used = 'unknown'

    try:
        disk = os.statvfs(path)
        capacity = disk.f_bsize * disk.f_blocks
        available = disk.f_bsize * disk.f_bavail
        used = disk.f_bsize * (disk.f_blocks - disk.f_bavail)
        human_available = bytes2human(available)
        human_capacity = bytes2human(capacity)
        human_used = bytes2human(used)
    except:
        logger.exception('Unable to gather disk usage information')
    finally:
        return {
            'available': human_available,
            'capacity': human_capacity,
            'used': human_used
        }


def shutdown_handler():
    global encoder
    global photo_overlay
    global play_list

    if encoder:
        encoder.stop()
    if photo_overlay:
        photo_overlay.stop()
    if play_list:
        play_list.stop()

atexit.register(shutdown_handler)
