### compile OpenCV
credits to [pyimagesearch](https://www.pyimagesearch.com/2019/09/16/install-opencv-4-on-raspberry-pi-4-and-raspbian-buster/)
#### increase swap-space
while this is generally a stupid idea, we need some additional memory while compiling opencv
```bash
sudo sed -i -e 's/^CONF_SWAPSIZE=.*$/CONF_SWAPSIZE=2048/g' /etc/dphys-swapfile
sudo /etc/init.d/dphys-swapfile restart
```
#### install compiler and required libraries
```bash
sudo apt-get install -y build-essential cmake pkg-config \
    libjpeg-dev libtiff5-dev libjasper-dev libpng-dev \
    libavcodec-dev libavformat-dev libswscale-dev libv4l-dev \
    libxvidcore-dev libx264-dev \
    libfontconfig1-dev libcairo2-dev \
    libgdk-pixbuf2.0-dev libpango1.0-dev \
    libgtk2.0-dev libgtk-3-dev \
    libatlas-base-dev gfortran \
    libhdf5-dev libhdf5-serial-dev libhdf5-103 \
    libqtgui4 libqtwebkit4 libqt4-test python3-pyqt5 \
    python3-dev python3-pip \
    libavresample4 libavresample-dev libopenjp3d7
    
sudo pip3 install "numpy" "picamera[array]"
```
#### download OpenCV
```bash
OPENCV_VERSION="4.5.2"
cd ~
rm opencv*.zip
wget -O opencv.zip https://github.com/opencv/opencv/archive/${OPENCV_VERSION}.zip
wget -O opencv_contrib.zip https://github.com/opencv/opencv_contrib/archive/${OPENCV_VERSION}.zip
unzip opencv.zip
unzip opencv_contrib.zip
mv -v opencv-${OPENCV_VERSION} opencv
mv -v opencv_contrib-${OPENCV_VERSION} opencv_contrib
```
#### compile OpenCV
```bash

rm -rf ~/opencv/build; mkdir ~/opencv/build
cd ~/opencv/build
# detect capabilities and optimize upcomming compile
time cmake -D CMAKE_BUILD_TYPE=RELEASE \
    -D CMAKE_INSTALL_PREFIX=/usr/local \
    -D OPENCV_EXTRA_MODULES_PATH=~/opencv_contrib/modules \
    -D ENABLE_NEON=ON \
    -D ENABLE_VFPV3=ON \
    -D BUILD_TESTS=OFF \
    -D INSTALL_PYTHON_EXAMPLES=OFF \
    -D OPENCV_ENABLE_NONFREE=ON \
    -D CMAKE_SHARED_LINKER_FLAGS=-latomic \
    -D BUILD_EXAMPLES=OFF ..
# watchout for 
#   - Python 3 interpreter is /usr/bin/python3
#   - OpenCV Modules do include Non-free algorithms: YES

# actually compile. Be aware:
# this will take ~1 1/2hours on a Raspi4, and up to 6hours on a Raspi3 B+
time make -j4 

# install this compiled version
sudo make install && sudo ldconfig
```

#### test
```bash
# this should report the same version as previously downloaded
echo -e "import cv2\nprint(cv2.__version__)" | python3
```

#### decrease swap-space
```bash
sudo sed -i -e 's/^CONF_SWAPSIZE=.*$/CONF_SWAPSIZE=100/g' /etc/dphys-swapfile
sudo /etc/init.d/dphys-swapfile restart
```


### bugfixes
if `echo -e "import cv2\nprint(cv2.__version__)" | python3` reports an error, try:
```bash
sudo apt-get reinstall libopenjp2-7

cd ~/opencv/build
sudo make uninstall
sudo make install

sudo ldconfig
```
