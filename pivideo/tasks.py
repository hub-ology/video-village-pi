from __future__ import absolute_import
import arrow
import datetime
import logging
import glob
import requests
import schedule
import time
from pivideo import play_list
from pivideo import omx
from pivideo.projector import Projector
from pivideo.sync import register_pi, current_show_schedule, report_current_pi_status

logger = logging.getLogger(__name__)

scheduled_show_active = False


def current_status():
    """
        Construct status information dictionary suitable for use
        with status reporting / status API
    """
    from pivideo import (play_list, photo_overlay, encoder, transcode_queue,
                         PI_HARDWARE_ADDRESS, cpu_temp, PI_IP_ADDRESS, version,
                         disk_usage, file_cache_size)

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
            if projector_status['on']:
                projector_status['position'] = p.position_status()
                projector_status['input_source'] = p.input_source()
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

    sd_card = disk_usage()
    sd_card['file_cache'] = file_cache_size()

    return {
        'hardware_address': PI_HARDWARE_ADDRESS,
        'ip_address': PI_IP_ADDRESS,
        'file_cache': glob.glob('/file_cache/*'),
        'scheduled_jobs': scheduled_jobs,
        'encoder': encoder_status,
        'play_list': play_list_status,
        'overlay': overlay_status,
        'projector': projector_status,
        'tunnels': tunnel_info,
        'cpu_temp': cpu_temp.temperature if cpu_temp else None,
        'version': version,
        'sd_card': sd_card
    }


def registration_task():
    """
        Register the Pi with the Video Village system
        This task will continue to attempt registration until the operation
        is successful.  This is to ensure temporary network disruptions
        do not impact the village pis from registering themselves.
    """
    try:
        if register_pi():
            # Once registration is confirmed, we'll stop running this task
            return schedule.CancelJob
    except:
        logger.exception('Problem registering this Pi with the Video Village')


def report_pi_status_task():
    """
        This task will periodically send Pi status information back to the
        Video Village system.
    """
    try:
        report_current_pi_status()
    except:
        logger.exception('Problem sending Pi status to the Video Village')


def pre_show_task():
    """
        This task runs prior to a showtime task to prepare the system for
        the show.  This primarily is to power on the attached projector
        and ensure the projector is properly configured.
    """
    global scheduled_show_active

    try:
        scheduled_show_active = True
        with Projector() as projector:
            if projector.power_on():
                time.sleep(5)
                projector.reset_settings()
                time.sleep(5)
                projector.rear_table_position()
                time.sleep(3)
                projector.input_source_hdmi()
                time.sleep(3)

        report_pi_status_task()
    except:
        logger.exception('Problem executing pre show set up')
    finally:
        return schedule.CancelJob


def post_show_task():
    """
        This task runs after a show is over to ensure the system returns
        to a proper "idle" state until it's time for the next show.
        Post show
    """
    global play_list
    global scheduled_show_active

    try:
        scheduled_show_active = False
        if play_list:
            play_list.stop()
    except:
        logger.exception('Problem stopping play list during post show clean up')

    try:
        with Projector() as projector:
            if projector.is_on():
                projector.power_off()

        report_pi_status_task()
    except:
        logger.exception('Problem powering off projector during post show clean up.  Was it connected and turned on?')
    finally:
        return schedule.CancelJob


def showtime_task(play_list_entries, loop=False):
    """
        This task is used to kick off a show at a scheduled time.
        It is provided with play list data based on the Video Village Window API
        JSON.
    """
    global play_list
    global scheduled_show_active

    try:
        scheduled_show_active = True
        play_list = omx.PlayList(play_list_entries, loop=loop)
        play_list.play()
        report_pi_status_task()
    except:
        logger.exception('Problem starting scheduled play list')
    finally:
        # Once the show is going, we'll stop running this task
        return schedule.CancelJob


def cache_files_task(play_list_entries):
    """
        Ensure all videos referenced in a play list are cached locally on the pi
    """
    try:
        play_list = omx.PlayList(play_list_entries)
        play_list.cache_entries()
        report_pi_status_task()
    except:
        logger.exception('Problem caching videos')
    else:
        # Once the videos have been cached, we'll cancel this task
        return schedule.CancelJob


def schedule_show(start_time, end_time, play_list_entries, loop=False):
    """
        Establish scheduled tasks necessary for a future show
    """
    # remove any existing show related tasks
    show_task_names = ('cache_files_task', 'pre_show_task', 'showtime_task', 'post_show_task')
    jobs_to_cancel = []
    for job in schedule.jobs:
        if job.job_func.func.func_name in show_task_names:
            jobs_to_cancel.append(job)
    for job in jobs_to_cancel:
        schedule.cancel_job(job)

    try:
        start_time_value = arrow.get(start_time, 'HH:mm')
    except ValueError:
        start_time_value = arrow.get(start_time, 'HH:mm:ss')

    try:
        end_time_value = arrow.get(end_time, 'HH:mm')
    except ValueError:
        end_time_value = arrow.get(end_time, 'HH:mm:ss')

    pre_show_time = (start_time_value - datetime.timedelta(minutes=2)).format('HH:mm')
    schedule.every(1).seconds.do(cache_files_task, play_list_entries)
    schedule.every().day.at(pre_show_time).do(pre_show_task)
    schedule.every().day.at(start_time_value.format('HH:mm')).do(showtime_task, play_list_entries, loop=loop)
    schedule.every().day.at(end_time_value.format('HH:mm')).do(post_show_task)


def fetch_show_schedule_task():
    """
        This task is used to periodically check for show schedule information
        The show information includes the play list of videos
        that the Pi should display during the show.
    """
    global scheduled_show_active

    try:
        current_show_info = current_show_schedule()
        # we'll only update our scheduled show tasks when we get back
        # information for our device and when there's not an active
        # show in progress (to avoid any disruption to the current show)
        if current_show_info and not scheduled_show_active:
            # Set up scheduled tasks to run the show
            loop = current_show_info.get('loop', False)
            play_list_entries = []
            schedule_playlist = current_show_info.get('playlist', {})
            for item in schedule_playlist.get('videosegment_set', []):
                video_link = item.get('video', {}).get('file')
                title = item.get('video', {}).get('title', '')
                subtitle = item.get('video', {}).get('uploader_name', '')
                play_list_entries.append({
                    'video': video_link
                })

            show = current_show_info.get('show', {})
            for item in show.get('scheduleitem_set', []):
                start_time = item.get('start_time')
                end_time = item.get('stop_time')
                if start_time and end_time:
                    schedule_show(start_time, end_time, play_list_entries, loop=loop)
        report_pi_status_task()
    except:
        logger.exception('Problem checking for show schedule information')


def setup_core_tasks():
    """
        Define the core tasks schedule
        This includes tasks to register the pi, check for scheduled show information, etc.
    """
    schedule.every(1).seconds.do(registration_task)
    schedule.every(15).minutes.do(report_pi_status_task)
    schedule.every(30).minutes.do(fetch_show_schedule_task)
