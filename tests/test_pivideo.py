from __future__ import absolute_import
from pivideo import seconds_until_next_heartbeat
import nose


def test_seconds_until_next_heartbeat():
    max_value = 60.0
    for i in range(60):
        next_heartbeat = seconds_until_next_heartbeat()
        nose.tools.assert_true(max_value >= next_heartbeat)
