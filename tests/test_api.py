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
        nose.tools.assert_false(response_data['encoder_active'])
        nose.tools.assert_false(response_data['player_active'])
        nose.tools.assert_equals([], response_data['transcode_queue'])
