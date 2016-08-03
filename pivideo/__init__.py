from __future__ import absolute_import
import atexit
import collections
import datetime
import logging
import socket
import fcntl
import requests
import schedule
import struct
import threading
import time
from pivideo import omx


logging.basicConfig(format='%(asctime)s	%(levelname)s:%(name)s:%(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


player = None
encoder = None

transcode_queue = collections.deque()


def get_ip_address(ifname):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return socket.inet_ntoa(fcntl.ioctl(
            s.fileno(),
            0x8915,  # SIOCGIFADDR
            struct.pack('256s', ifname[:15])
        )[20:24])
    except IOError:
        return ''


def get_hardware_address(ifname):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        info = fcntl.ioctl(s.fileno(), 0x8927,  struct.pack('256s', ifname[:15]))
        return ''.join(['%02x:' % ord(char) for char in info[18:24]])[:-1]
    except IOError:
        return ''


def register_pi():
    mac_address = get_hardware_address('eth0')
    if mac_address:
        result = requests.post('http://videovillage.seeingspartanburg.com/api/pis/register/',
                               headers={'X-HUBOLOGY-VIDEO-VILLAGE-PI': mac_address},
                               json={'mac_address': mac_address})
        logger.info(result.content)
        #TODO: add retry on failures such that registration is attempted again
        #      until it's successful


def seconds_until_next_heartbeat():
    now = datetime.datetime.utcnow()
    return 60.0 - (now.second + (now.microsecond * 0.000001))


def heartbeat():
    global encoder
    global heartbeat_timer

    register_pi()

    while True:
        try:
            time.sleep(seconds_until_next_heartbeat())
            logger.info('heartbeat')
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
            schedule.run_pending()
        except:
            logger.exception('Error during heartbeat timer processing:')


heartbeat_thread = threading.Thread(target=heartbeat)
heartbeat_thread.daemon = True
heartbeat_thread.start()


def shutdown_handler():
    if player:
        player.stop()
    if encoder:
        encoder.stop()

atexit.register(shutdown_handler)
