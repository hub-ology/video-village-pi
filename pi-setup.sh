# set up fresh raspbian jessy lite install for video village usage
# https://downloads.raspberrypi.org/raspbian_lite_latest
sudo apt-get update

# Video Village Pis will use omxplayer for video playback
sudo apt-get install -y omxplayer

# use GStreamer for video transcoding
sudo apt-get install -y libgstreamer1.0-0 libgstreamer1.0-0-dbg \
                        libgstreamer1.0-dev liborc-0.4-0 liborc-0.4-0-dbg \
                        liborc-0.4-dev liborc-0.4-doc \
                        gir1.2-gst-plugins-base-1.0 gir1.2-gstreamer-1.0 \
                        gstreamer1.0-alsa gstreamer1.0-doc gstreamer1.0-omx \
                        gstreamer1.0-plugins-bad gstreamer1.0-plugins-bad-dbg \
                        gstreamer1.0-plugins-bad-doc gstreamer1.0-plugins-base \
                        gstreamer1.0-plugins-base-apps \
                        gstreamer1.0-plugins-base-dbg \
                        gstreamer1.0-plugins-base-doc gstreamer1.0-plugins-good \
                        gstreamer1.0-plugins-good-dbg gstreamer1.0-plugins-good-doc \
                        gstreamer1.0-plugins-ugly gstreamer1.0-plugins-ugly-dbg \
                        gstreamer1.0-plugins-ugly-doc gstreamer1.0-pulseaudio \
                        gstreamer1.0-tools gstreamer1.0-x \
                        libgstreamer-plugins-bad1.0-0 \
                        libgstreamer-plugins-bad1.0-dev \
                        libgstreamer-plugins-base1.0-0 \
                        libgstreamer-plugins-base1.0-dev


#Set up Python related components
sudo apt-get install -y libffi5 python-virtualenv git
curl -L https://bitbucket.org/pypy/pypy/downloads/pypy2-v5.3.1-linux-armhf-raspbian.tar.bz2 \
     -o pypy2-v5.3.1-linux-armhf-raspbian.tar.bz2
sudo tar -xjf pypy2-v5.3.1-linux-armhf-raspbian.tar.bz2 -C /usr/local --strip-components=1

virtualenv -p pypy video-env
source video-env/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

#TODO: set up services to keep video village pi API running after restarts, etc

#TODO: use nginx with https://letsencrypt.org for SSL certificate management

#TODO: configure remote access and monitoring
