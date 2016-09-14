# Utility functions for keeping each Video Pi in sync with the
# overall Video Village.   Pis will register themselves at start up
# and periodically report status information
from __future__ import absolute_import
import datetime
import logging
import requests
from pivideo import PI_HARDWARE_ADDRESS

logger = logging.getLogger(__name__)

#TODO: make callbacks over https
BASE_VILLAGE_URL = 'http://videovillage.seeingspartanburg.com'
VILLAGE_REGISTER_ENDPOINT = '{0}/api/pis/register/'.format(BASE_VILLAGE_URL)
VILLAGE_WINDOWS_ENDPOINT = '{0}/api/windows/'.format(BASE_VILLAGE_URL)
VILLAGE_PI_STATUS_ENDPOINT = '{0}/api/pis/{1}/status/'.format(BASE_VILLAGE_URL, '{0}')

VILLAGE_REQUEST_HEADERS = {
    'X-HUBOLOGY-VIDEO-VILLAGE-PI': PI_HARDWARE_ADDRESS
}

video_village_pi_id = None


def register_pi():
    """
        Registers this Pi with the Video Village via the pis register API
        If the Pi receives a successful response, we'll update our assigned
        video village pi id for later use.
    """
    global video_village_pi_id
    result = requests.post(VILLAGE_REGISTER_ENDPOINT,
                           headers=VILLAGE_REQUEST_HEADERS,
                           json={'mac_address': PI_HARDWARE_ADDRESS})
    if result.status_code == 200:
        registration_info = result.json()
        video_village_pi_id = registration_info.get('id')
        return True

    return False


def report_current_pi_status():
    """
        Report current Pi status information to the Video Village system
    """
    global video_village_pi_id
    from pivideo import current_status

    result = requests.post(VILLAGE_PI_STATUS_ENDPOINT.format(video_village_pi_id),
                           headers=VILLAGE_REQUEST_HEADERS,
                           json=current_status())
    if result.status_code == 200:
        return True

    return False


def current_show_schedule():
    """
        Request show schedule information for this Pi for the current date
    """
    today = datetime.date.today()

    result = requests.get(VILLAGE_WINDOWS_ENDPOINT,
                          headers=VILLAGE_REQUEST_HEADERS,
                          params={
                            'mac_address': PI_HARDWARE_ADDRESS,
                            'show_date': today.strftime('%Y-%m-%d')
                          })

    logger.info('{0} {1}'.format(result.status_code, result.content))
    if result.status_code == 200:
        schedule_information = result.json()
        return schedule_information

    return None
