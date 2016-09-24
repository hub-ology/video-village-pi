from __future__ import absolute_import
import json
from pivideo.api import app
import nose
import schedule


def test_status_api():
    """
        Verify status API returns a proper response
    """

    with app.test_client() as client:
        response = client.get('/status')
        nose.tools.assert_equals(200, response.status_code)
        response_data = json.loads(response.data)
        nose.tools.assert_false(response_data['encoder']['active'])
        nose.tools.assert_false(response_data['overlay']['active'])
        nose.tools.assert_false(response_data['play_list']['active'])
        nose.tools.assert_false(response_data['projector']['connected'])
        nose.tools.assert_equals([], response_data['encoder']['queue'])
        nose.tools.assert_equals(response_data['version'], 'v0.5')
        nose.tools.assert_in('hardware_address', response_data)
        nose.tools.assert_in('ip_address', response_data)

def test_play_stop():
    """
        Verify play API stop operation when no video has been played
    """
    with app.test_client() as client:
        response = client.post('/play', data=json.dumps({}), content_type='application/json')
        nose.tools.assert_equals(200, response.status_code)
        response_data = json.loads(response.data)
        nose.tools.assert_equals('stopped', response_data['status'])


def test_play_scheduled():
    """
        Verify play API schedule operation to queue up a show in the future
    """
    initial_job_count = len(schedule.jobs)
    with app.test_client() as client:
        request_data = {
            "play_list": [
                {
                    "photo": "https://s3.amazonaws.com/pivideo-testing/ssnl_logo.png",
                    "duration": 5
                },
                {
                    "video": "https://s3.amazonaws.com:443/hubology-video-village-media/media/DJI_0127.MOV"
                }
            ],
            "loop": True,
            "start_time": "04:00",
            "end_time": "04:30"
        }
        response = client.post('/play', data=json.dumps(request_data),
                               content_type='application/json')
        nose.tools.assert_equals(200, response.status_code)
        response_data = json.loads(response.data)
        nose.tools.assert_equals('scheduled', response_data['status'])
        job_count = len(schedule.jobs)
        task_names = [job.job_func.func.func_name for job in schedule.jobs]
        nose.tools.assert_equals(job_count, initial_job_count + 4)
        nose.tools.assert_equals(task_names.count('cache_files_task'), 1)
        nose.tools.assert_equals(task_names.count('pre_show_task'), 1)
        nose.tools.assert_equals(task_names.count('showtime_task'), 1)
        nose.tools.assert_equals(task_names.count('post_show_task'), 1)
        schedule.clear()

def test_projector_on_not_connected():
    """
        Verify proper handling of a POST /projector/on when no projector is connected
    """
    with app.test_client() as client:
        response = client.post('/projector/on', data=json.dumps({}), content_type='application/json')
        nose.tools.assert_equals(200, response.status_code)
        response_data = json.loads(response.data)
        nose.tools.assert_false(response_data['status'])


def test_projector_off_not_connected():
    """
        Verify proper handling of a POST /projector/off when no projector is connected
    """
    with app.test_client() as client:
        response = client.post('/projector/off', data=json.dumps({}), content_type='application/json')
        nose.tools.assert_equals(200, response.status_code)
        response_data = json.loads(response.data)
        nose.tools.assert_false(response_data['status'])
