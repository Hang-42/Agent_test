#!/usr/bin/env bash
set -eo pipefail
source /opt/ros/humble/setup.bash
export ROS_DOMAIN_ID=83
exec python3 /scripts/scene_skill.py "$1"
