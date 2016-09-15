from __future__ import absolute_import
import nose
from pivideo.tasks import schedule_show
import schedule


def test_remove_overlapping_show_tasks():
    """
        Ensure on demand scheduling of a show removes any overlapping tasks
    """
    play_list_entries = [
        {
            "video": "https://s3.amazonaws.com:443/hubology-video-village-media/media/DJI_0127.MOV"
        },
        {
            "photo": "https://s3.amazonaws.com/pivideo-testing/ssnl_logo.png",
            "duration": 30
        }
    ]

    initial_job_count = len(schedule.jobs)
    schedule_show('20:00', '22:00', play_list_entries, loop=True)

    job_count = len(schedule.jobs)
    task_names = [job.job_func.func.func_name for job in schedule.jobs]
    nose.tools.assert_equals(job_count, initial_job_count + 4)
    nose.tools.assert_equals(task_names.count('cache_files_task'), 1)
    nose.tools.assert_equals(task_names.count('pre_show_task'), 1)
    nose.tools.assert_equals(task_names.count('showtime_task'), 1)
    nose.tools.assert_equals(task_names.count('post_show_task'), 1)

    schedule_show('20:00', '22:00', play_list_entries, loop=True)
    task_names = [job.job_func.func.func_name for job in schedule.jobs]
    nose.tools.assert_equals(task_names.count('cache_files_task'), 1)
    nose.tools.assert_equals(task_names.count('pre_show_task'), 1)
    nose.tools.assert_equals(task_names.count('showtime_task'), 1)
    nose.tools.assert_equals(task_names.count('post_show_task'), 1)
