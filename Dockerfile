FROM resin/rpi-raspbian
USER root
# Install python and some barebones tools
# (Things you would typically have in the Pi's environment)
RUN apt-get update && \
    apt-get install -y -q \
    wget \
    git \
    vim \
    locales \
    build-essential \
    python \
    libpython-dev \
    libboost-chrono-dev \
    libboost-date-time-dev \
    libboost-program-options-dev \
    libboost-regex-dev \
    libboost-system-dev \
    libboost-thread-dev \
    libtinyxml-dev \
    libboost-filesystem-dev \
    libxml2-dev \
    libgtest-dev
# Tell apt to read from the ROS package repository
RUN sudo sh -c 'echo "deb http://packages.ros.org/ros/ubuntu jessie main" > /etc/apt/sources.list.d/ros-latest.list'
RUN wget https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -O - | sudo apt-key add -
RUN sudo locale-gen en_US.UTF-8
# Create pi user
RUN useradd pi && echo 'pi:hypriot' | chpasswd && echo "pi ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers && mkdir -p /home/pi && chown pi:pi /home/pi

USER pi
WORKDIR /home/pi/
# Give the pi user access to the usb drive for flashing an Arduino
RUN sudo usermod -a -G dialout pi
# Add catkin install dir (built with catkin)
# Note that you must run docker builds from ~/catkin_ws
#
#    cd ~/catkin_ws
#    docker build -f ./src/openag_brain/Dockerfile .
#
# We use COPY rather than ADD, as COPY is preferred for local files.
# https://docs.docker.com/engine/userguide/eng-image/dockerfile_best-practices/#add-or-copy
COPY . /home/pi/catkin_ws
RUN sudo chown -R pi:pi ~/catkin_ws
# Install ROS boostrapping tool
RUN sudo apt-get update && sudo apt-get install --no-install-recommends -y -q \
    python-pip python-rosdep

# Install some python dependencies that there aren't ros packages for.
RUN sudo pip install -q voluptuous 

# Install dependencies with rosdep
RUN sudo rosdep init && rosdep update && rosdep install --from-paths ~/catkin_ws/src --ignore-src --rosdistro indigo -y -r --os=debian:jessie
RUN cd ~/catkin_ws && ./src/catkin/bin/catkin_make install
# Add .bashrc
RUN echo -e '[ -z "$PS1" ] && return' >~/.bashrc
RUN echo -e 'source ~/catkin_ws/install/setup.bash' >>~/.bashrc

# Set up ROS environment vars
ENV LANG=en_US.UTF-8 ROS_DISTRO=indigo
# Run the project
CMD ["/home/pi/catkin_ws/install/env.sh", "rosrun", "openag_brain", "main", "personal_food_computer_v2.launch"]
USER pi
