from __future__ import absolute_import
import json
from pivideo.api import app
import nose


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
        nose.tools.assert_false(response_data['player']['active'])
        nose.tools.assert_false(response_data['play_list']['active'])
        nose.tools.assert_false(response_data['projector']['connected'])
        nose.tools.assert_equals([], response_data['encoder']['queue'])

def test_play_stop():
    """
        Verify play API stop operation when no video has been played
    """
    with app.test_client() as client:
        response = client.post('/play', data=json.dumps({}), content_type='application/json')
        nose.tools.assert_equals(200, response.status_code)
        response_data = json.loads(response.data)
        nose.tools.assert_equals('stopped', response_data['status'])


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
