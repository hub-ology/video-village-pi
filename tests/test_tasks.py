from __future__ import absolute_import
from httmock import all_requests, HTTMock
import nose
from pivideo.tasks import schedule_show, fetch_show_schedule_task
import schedule


example_show_schedule_response = [
    {
        "id": 4,
        "loop": False,
        "offset_in_show": 0,
        "playlist": {
            "notes": "",
            "title": "Test",
            "videosegment_set": [
                {
                    "duration": 60,
                    "offset_in_playlist": 0,
                    "offset_in_video": 0,
                    "video": {
                        "address": "",
                        "approved": False,
                        "category": "",
                        "city": "",
                        "description": "Test run",
                        "email": "testuser1@example.com",
                        "file": "https://s3.amazonaws.com:443/hubology-video-village-media/media/IMG_6794.MOV",
                        "id": 5,
                        "length": None,
                        "moderated_by": None,
                        "moderation_notes": None,
                        "phone": "",
                        "state": None,
                        "status": "s",
                        "title": "submission test",
                        "uploader_name": "Jane Doe",
                        "zipcode": ""
                    }
                }
            ]
        },
        "repeats": 5,
        "show": {
            "scheduleitem_set": [
                {
                    "date": "2016-09-16",
                    "id": 4,
                    "show": "   3: Hubology Test Show",
                    "start_time": "20:15:00",
                    "stop_time": "22:45:00"
                }
            ]
        },
        "window": 53
    }
]


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


def test_map_play_list_information():
    """
        Verify proper mapping of Pi Window Schedule Information to a set of show tasks
    """
    # clear any currently scheduled items
    schedule.clear()

    # set up a mock Pi Windows API response for testing
    @all_requests
    def window_response_content(url, request):
        return {
            'status_code': 200,
            'content': example_show_schedule_response
        }

    # fire off the task that periodically checks for show updates
    with HTTMock(window_response_content):
        fetch_show_schedule_task()

    # verify we have the proper tasks queued up to run the show
    task_names = [job.job_func.func.func_name for job in schedule.jobs]
    nose.tools.assert_equals(task_names.count('cache_files_task'), 1)
    nose.tools.assert_equals(task_names.count('pre_show_task'), 1)
    nose.tools.assert_equals(task_names.count('showtime_task'), 1)
    nose.tools.assert_equals(task_names.count('post_show_task'), 1)
