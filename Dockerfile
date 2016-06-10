FROM pablogn/rpi-ros-core-indigo

# Set up a catkin workspace
USER pi
RUN mkdir -p ~/catkin_ws/src && cd ~/catkin_ws/src && \
    /opt/ros/indigo/env.sh catkin_init_workspace
ADD . catkin_ws/src/openag_brain
# TODO: Remove this when rosdistro merges our pull request
RUN sudo sh -c 'echo "yaml https://raw.github.com/OpenAgInitiative/rosdistro/master/rosdep/python.yaml" > \
    /etc/ros/rosdep/sources.list.d/19-custom.list' && rosdep update
RUN sudo chown -R pi:pi ~/catkin_ws/src/openag_brain && cd ~/catkin_ws && \
    /opt/ros/indigo/env.sh catkin_make && sudo apt-get update && \
    sudo apt-get install -y python-pip && \
    ~/catkin_ws/devel/env.sh rosdep install -i -y openag_brain

CMD ["~/catkin_ws/devel/env.sh", "rosrun", "openag_brain", "main"]