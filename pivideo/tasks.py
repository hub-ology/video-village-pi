from __future__ import absolute_import
import logging
import schedule
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
    finally:
        return schedule.CancelJob


def post_show_task():
    """
        This task runs after a show is over to ensure the system returns
        to a proper "idle" state until it's time for the next show.
        Post show
    """
    from pivideo import play_list

    try:
        with Projector() as projector:
            if projector.is_on():
                projector.power_off()
        if play_list:
            play_list.stop()
    finally:
        return schedule.CancelJob


def showtime_task(play_list_videos):
    """
        This task is used to kick off a show at a scheduled time.
        It is provided with play list data based on the Video Village Window API
        JSON.
    """
    from pivideo import play_list

    try:
        print(play_list_data)
        play_list = omx.PlayList(play_list_videos, loop=False)
        play_list.play()
    finally:
        # Once the show is over, we'll stop running this task
        return schedule.CancelJob


def schedule_show(start_time, end_time, play_list_videos):
    """
        Establish scheduled tasks necessary for a future show
    """
    schedule.every().day.at('').do(pre_show_task)
    schedule.every().day.at(start_time).do(showtime_task, play_list_videos)
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
            schedule_show('', '', [])
    except:
        logger.exception('Problem checking for show schedule information')
