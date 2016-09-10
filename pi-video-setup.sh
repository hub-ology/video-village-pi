# set up fresh raspbian jessy lite install for video village usage
# https://downloads.raspberrypi.org/raspbian_lite_latest

unzip-strip() (
    local zip=$1
    local dest=${2:-.}
    local temp=$(mktemp -d) && unzip -d "$temp" "$zip" && mkdir -p "$dest" &&
    shopt -s dotglob && local f=("$temp"/*) &&
    if (( ${#f[@]} == 1 )) && [[ -d "${f[0]}" ]] ; then
        mv "$temp"/*/* "$dest"
    else
        mv "$temp"/* "$dest"
    fi && rmdir "$temp"/* "$temp"
)

sudo apt-get update
sudo apt-get upgrade

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

# make sure git is available to clone code for pngview
sudo apt-get install -y git
# Ensure libjpeg is available for working with photos
sudo apt-get install -y libjpeg-dev

# build and install the pngview utility
git clone https://github.com/AndrewFromMelbourne/raspidmx.git
cd raspidmx/pngview
make
sudo cp pngview /usr/local/bin/
cd -

#Set up Python related components
sudo apt-get install -y libffi5 python-virtualenv
curl -L https://bitbucket.org/pypy/pypy/downloads/pypy2-v5.3.1-linux-armhf-raspbian.tar.bz2 \
     -o pypy2-v5.3.1-linux-armhf-raspbian.tar.bz2
sudo tar -xjf pypy2-v5.3.1-linux-armhf-raspbian.tar.bz2 -C /usr/local --strip-components=1

curl -L https://github.com/hub-ology/video-village-pi/archive/master.zip -o video-village-pi.zip
unzip-strip video-village-pi.zip

virtualenv -p pypy video-env
source video-env/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# set up file cache directory
sudo mkdir -p /file_cache
sudo chmod 777 /file_cache

#set up services to keep video village pi API running after restarts, etc
sudo cp systemd/pivideo.service /etc/systemd/system/pivideo.service
sudo systemctl enable /etc/systemd/system/pivideo.service
sudo systemctl start pivideo.service

#set up ngrok tunnel services for remote access and management
sudo cp systemd/ngrok.service /etc/systemd/system/ngrok.service
sudo systemctl enable /etc/systemd/system/ngrok.service
sudo systemctl start ngrok.service

echo "Be sure to set gpu_mem=128 (or a higher value) in /boot/config.txt for best HD video handling"
#TODO: also set GPU memory value to at least `gpu_mem=128` in /boot/config.txt ?
