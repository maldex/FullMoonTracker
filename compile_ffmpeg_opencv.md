# Compile FFMPEG and OpenCV for Raspberry OS

# prepare Raspi 
```
# update
sudo apt-get update && sudo apt-get full-upgrade -y
echo "y" | sudo rpi-update

# increase swap space
sudo sed -i -e 's/^CONF_SWAPSIZE=.*$/CONF_SWAPSIZE=2048/g' /etc/dphys-swapfile
sudo /etc/init.d/dphys-swapfile restart

# allow /usr/local to be used by the current user
sudo setfacl -m u:`whoami`:rwX /usr/local/src/

libcamera-hello --list-cameras
sudo vclog -m | grep -i imx
dmesg | grep -i imx
vcgencmd get_camera
i2cdetect -y 10

sudo reboot
```

---
# install rtsp-simple-server
```
pushd /usr/local/src
wget -qO - https://github.com/bluenviron/mediamtx/releases/download/v0.23.5/mediamtx_v0.23.5_linux_arm64v8.tar.gz | tar -zxvf - 
rm LICENSE
sudo cp -v mediamtx /usr/local/bin
sudo cp -v mediamtx.yml /etc/

# https://github.com/bluenviron/mediamtx/blob/main/mediamtx.yml
cat << EOF | sudo tee /etc/mediamtx.yml  > /dev/null
paths:
  cam:
    source: rpiCamera
    rpiCameraWidth: 1280
    rpiCameraHeight: 720
    rpiCameraTextOverlayEnable: true
    rpiCameraTextOverlay: '%Y-%m-%d %H:%M:%S - HOSTNAME'
  all:
EOF

sudo sed -i 's/HOSTNAME/'$(hostname -s)'/g' /etc/mediamtx.yml

cat << EOF > ~pi/mediamtx.service
[Unit]
Wants=network.target
User=pi
[Service]
ExecStart=/usr/local/bin/mediamtx /etc/mediamtx.yml
[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable --now ~pi/mediamtx.service
```
-> rtsp://10.83.6.99:8554/cam

# install build system
```bash
cd /usr/local/src; numcpu=`grep "processor" /proc/cpuinfo | wc -l`

sudo apt-get install -y build-essential autoconf automake cmake pkg-config \
    libjpeg-dev libtiff5-dev libpng-dev git libavcodec-dev libavformat-dev libswscale-dev libv4l-dev \
    libxvidcore-dev libx264-dev libfontconfig1-dev libcairo2-dev libgdk-pixbuf2.0-dev libpango1.0-dev \
    libgtk2.0-dev libgtk-3-dev libatlas-base-dev gfortran libgtkglext1-dev libgtkglext1\
    libhdf5-dev libhdf5-serial-dev libhdf5-103 python3-pyqt5 python3-dev python3-pip \
    libavresample4 libavresample-dev libopenjp3d7 libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev \
    liblog4cpp5-dev libv4l-dev libasound2-dev libalsaplayer-dev libclalsadrv-dev libdssialsacompat-dev \
    liblivemedia-dev libgroupsock8 libbasicusageenvironment1 libcaca-dev libssl-dev \
    libass-dev libfreetype6-dev libgnutls28-dev libmp3lame-dev libsdl2-dev libtool  libva-dev libvdpau-dev \
    libvorbis-dev libxcb1-dev libxcb-shm0-dev libxcb-xfixes0-dev meson ninja-build pkg-config texinfo \
    yasm zlib1g-dev nasm libx264-dev libx265-dev libnuma-dev  libvpx-dev libopus-dev \
    libdav1d-dev libtesseract4 libtesseract-dev libdc1394-25 libdc1394-dev libeigen3-dev liblapack-dev \
    libblas-dev libopenblas-pthread-dev liblapacke-dev 
```
# install ffmpeg 5.0.1   (~45min)
```bash
cd /usr/local/src; numcpu=`grep "processor" /proc/cpuinfo | wc -l`
wget -qO - http://www.ffmpeg.org/releases/ffmpeg-5.0.1.tar.gz | tar -zxvf -
pushd ffmpeg-5.0.1
time ./configure --enable-shared --enable-gpl --enable-libx264 --enable-libx265 --enable-libvpx --enable-zlib --enable-pic
time make -j$numcpu    # 40min
sudo make install && sudo ldconfig
popd
```

# install OpenCV 4.7.0 (~160min)
```bash
cd /usr/local/src; numcpu=`grep "processor" /proc/cpuinfo | wc -l`

wget -qO - https://github.com/opencv/opencv/archive/refs/tags/4.7.0.tar.gz | tar -zxvf - 
wget -qO - https://github.com/opencv/opencv_contrib/archive/refs/tags/4.7.0.tar.gz | tar -zxvf - 

mkdir -p ./opencv_build; cd ./opencv_build 

# detect capabilities and optimize upcomming compile
time cmake -D CMAKE_BUILD_TYPE=RELEASE \
    -D CMAKE_INSTALL_PREFIX=/usr/local \
    -D OPENCV_EXTRA_MODULES_PATH=`pwd`/../opencv_contrib-4.7.0/modules \
    -D BUILD_TESTS=OFF -D BUILD_PERF_TESTS=OFF \
    -D INSTALL_PYTHON_EXAMPLES=OFF -D BUILD_EXAMPLES=OFF \
    -D OPENCV_ENABLE_NONFREE=ON \
    -D OPENCV_GENERATE_PKGCONFIG=ON \
    -D CMAKE_SHARED_LINKER_FLAGS=-latomic \
    -D PYTHON3_PACKAGES_PATH=/usr/lib/python3/dist-packages \
    ../opencv-4.7.0/

# watchout for 
#   - Python 3 interpreter is /usr/bin/python3
#   - OpenCV Modules do include Non-free algorithms: YES

time cmake --build . --config Release -- -j $numcpu    # 160min

sudo make install && sudo ldconfig

pkg-config --modversion opencv4
python3 -c "import cv2; print(cv2.__version__)"

popd
```

# cleanup
```
# decrease swap space
sudo sed -i -e 's/^CONF_SWAPSIZE=.*$/CONF_SWAPSIZE=256/g' /etc/dphys-swapfile
sudo /etc/init.d/dphys-swapfile restart
```

# try
```python
#!/usr/bin/python3
# -*- coding: utf-8 -*-
import cv2
import numpy as np
import os, random
os.environ["DISPLAY"] = "poseidon:0"
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"
#vcap = cv2.VideoCapture("rtsp://10.83.6.197:8554/cam", cv2.CAP_FFMPEG)  
vcap = cv2.VideoCapture("rtsp://127.0.0.1:8554/cam", cv2.CAP_FFMPEG)  #"rtmp://10.83.6.197/cam"

while(1):
    ret, frame = vcap.read()
    if ret == False:
        print("Frame is empty")
        break;
    else:
        cv2.circle(frame, (50, 50), 25, (random.randrange(0,256), random.randrange(0,256), random.randrange(0,256)), 3)
        cv2.imshow('VIDEO', frame)
        cv2.waitKey(1)
```






```python
#!/usr/bin/python3
# -*- coding: utf-8 -*-
import cv2
import numpy
import os, random, time, pprint
os.environ["DISPLAY"] = "poseidon:0"
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"
#vcap = cv2.VideoCapture("rtsp://10.83.6.197:8554/cam", cv2.CAP_FFMPEG)  
vcap = cv2.VideoCapture("rtsp://127.0.0.1:8554/cam", cv2.CAP_FFMPEG)  #"rtmp://10.83.6.197/cam"

c={
    "dp": 1.4,
    "minDist_divider": 8,
    "minRadius_divider": 64,
    "maxRadius_divider": 2
}

while(1):
    ret, frame = vcap.read()
    if ret == False:
        print("Frame is empty")
        break;
    else:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        cv2.circle(frame, (50, 50), 25, (random.randrange(0,256), random.randrange(0,256), random.randrange(0,256)), 3)
        
        stime = time.time()
        circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, dp=c['dp'], minDist=int(gray.shape[0]/c['minDist_divider']), minRadius=int(gray.shape[0]/c['minRadius_divider']), maxRadius=int(gray.shape[0]/c['maxRadius_divider']))
        circles = numpy.round(circles[0, :]).astype("int")
        delta = int((time.time() - stime) * 1000 * 1000 ) / 1000
        pprint.pprint(circles)
        print("found " + str(len(circles)) + " circles in " + str(delta))


        dX, dY = None, None
        for (x, y, r) in circles:
            # draw the circle in the output image, then draw a rectangle
            # corresponding to the center of the circle
            print("circle at " + str((x,y,r)))
            cir = (x,y,r)
            cv2.line(frame, (x - 5, y - 5), (x + 5, y + 5), other_color, 1)
            cv2.line(frame, (x - 5, y + 5), (x + 5, y - 5), other_color, 1)

        cv2.imshow('VIDEO', frame)
        cv2.waitKey(1)
```