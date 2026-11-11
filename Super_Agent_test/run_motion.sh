#!/usr/bin/env bash
set -eo pipefail
source /opt/ros/humble/setup.bash
export ROS_DOMAIN_ID=83
exec python3 /scripts/robot_motion.py
