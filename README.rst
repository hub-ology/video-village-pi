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

    ./pi-video-setup.sh

After the dependencies have been installed, you may source the virtual environment
that was created by the set up script by running:
::

    source video-env/bin/activate

This will ensure that you have all of the necessary Python dependencies
readily available for running the project's tests or the WSGI HTTP server
to provide the API services.


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
      "encoder": {
        "active": false,
        "queue": []
      },
      "hardware_address": "00:00:00:00:00:00",
      "overlay": {
        "active": true,
        "layer": 2,
        "photo": "/file_cache/demo.png",
        "x": 0,
        "y": 900
      },
      "player": {
        "active": false,
        "audio": {},
        "mediafile": null,
        "video": {}
      }
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

You may also provide a URL in the video parameter to the play API and the Pi will fetch and cache
the video prior to playing it.

Show an image overlay on the Pi above a video:

::

    curl -H "Content-Type: application/json" -XPOST -d '{"photo": "overlay.png"}' http://IP_ADDRESS:5000/overlay
    {
      "status": "active"
    }

Stop/remove the current photo overlay

::


    curl -H "Content-Type: application/json" -XPOST -d '{}' http://IP_ADDRESS:5000/overlay
    {
      "status": "stopped"
    }


Transcode a video that's been previously sync'ed to the Pi

::

    curl -H "Content-Type: application/json" -XPOST -d '{"source_file": "test.mp4", "target_file": "test_800x600.mp4", "width": 800, "height": 600}' http://IP_ADDRESS:5000/transcode
    {
    "status": "queued"
    }
