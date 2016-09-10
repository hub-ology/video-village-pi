from __future__ import absolute_import
import arrow
import datetime
import logging
import schedule
from pivideo import play_list
from pivideo import omx
from pivideo.projector import Projector
from pivideo.sync import register_pi, current_show_schedule

logger = logging.getLogger(__name__)


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


def pre_show_task():
    """
        This task runs prior to a showtime task to prepare the system for
        the show.  This primarily is to power on the attached projector
        and ensure the projector is properly configured.
    """
    try:
        with Projector() as projector:
            if projector.power_on():
                projector.reset_settings()
                projector.rear_table_position()
                projector.input_source_hdmi()
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

    try:
        with Projector() as projector:
            if projector.is_on():
                projector.power_off()
        if play_list:
            play_list.stop()
    except:
        logger.exception('Problem executing post show clean up')
    finally:
        return schedule.CancelJob


def showtime_task(play_list_entries, loop=False):
    """
        This task is used to kick off a show at a scheduled time.
        It is provided with play list data based on the Video Village Window API
        JSON.
    """
    global play_list
    try:
        play_list = omx.PlayList(play_list_entries, loop=loop)
        play_list.play()
    except:
        logger.exception('Problem starting scheduled play list')
    finally:
        # Once the show is going, we'll stop running this task
        return schedule.CancelJob


def cache_videos_task(play_list_entries):
    """
        Ensure all videos referenced in a play list are cached locally on the pi
    """
    try:
        play_list = omx.PlayList(play_list_entries)
        play_list.cache_entries()
    except:
        logger.exception('Problem caching videos')
    else:
        # Once the videos have been cached, we'll cancel this task
        return schedule.CancelJob


def schedule_show(start_time, end_time, play_list_entries, loop=False):
    """
        Establish scheduled tasks necessary for a future show
    """
    schedule.every(1).seconds.do(cache_videos_task, play_list_entries)
    pre_show_time = (arrow.get(start_time, 'HH:mm') - datetime.timedelta(minutes=2)).format('HH:mm')
    schedule.every().day.at(pre_show_time).do(pre_show_task)
    schedule.every().day.at(start_time).do(showtime_task, play_list_entries, loop=loop)
    schedule.every().day.at(end_time).do(post_show_task)


def fetch_show_schedule_task():
    """
        This task is used to periodically check for show schedule information
        The show information includes the play list of videos
        that the Pi should display during the show.
    """
    try:
        current_show = current_show_schedule()
        if current_show:
            # Set up scheduled tasks to run the show
            # TODO: map village windows API response to a scheduled pi show
            #schedule_show('', '', [])
            pass
    except:
        logger.exception('Problem checking for show schedule information')


def setup_core_tasks():
    """
        Define the core tasks schedule
        This includes tasks to register the pi, check for scheduled show information, etc.
    """
    schedule.every(1).seconds.do(registration_task)
    schedule.every(30).minutes.do(fetch_show_schedule_task)
