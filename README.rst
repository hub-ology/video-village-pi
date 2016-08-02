video village pi
================
The software and services powering each Raspberry Pi installed in
the Video Village as part of http://seeingspartanburg.com

Installation:
-------------
With a fresh SD card based on https://downloads.raspberrypi.org/raspbian_lite_latest ,
you can run the pi-setup.sh script to install the necessary
dependencies.
::

    ./pi-setup.sh


Starting the API services
-------------------------
The Video Village Raspberry Pi API may be deployed and run
using your favorite WSGI HTTP server.  Here's an example using gunicorn:

::

    gunicorn -w 1 -b 0.0.0.0:5000 pivideo.api:app


Interacting with the Video Village Raspberry Pis
------------------------------------------------

Check the status information for a specific Pi

::

    curl http://IP_ADDRESS:5000/status
    {
      "encoder_active": false,
      "hardware_address": "00:00:00:00:00:00",
      "player_active": false
    }

Play a specific video that's been previously sync'ed to the Pi

::

    curl -H "Content-Type: application/json" -XPOST -d '{"video": "test.mp4"}' http://IP_ADDRESS:5000/play
    {
      "audio": {
      "bps": 16,
      "channels": 6,
      "decoder": "aac",
      "rate": 48000
      },
      "status": "running",
      "video": {
      "decoder": "omx-h264",
      "dimensions": [
        640,
        480
      ],
      "fps": 25.0,
      "profile": 77
      }
    }

Transcode a video that's been previously sync'ed to the Pi

::

    curl -H "Content-Type: application/json" -XPOST -d '{"source_file": "test.mp4", "target_file": "test_800x600.mp4", "width": 800, "height": 600}' http://IP_ADDRESS:5000/transcode
    {
    "status": "queued"
    }
