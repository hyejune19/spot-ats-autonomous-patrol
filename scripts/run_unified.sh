#!/usr/bin/env bash
set -euo pipefail
: "${SPOTATS_WORKSPACE:?Set SPOTATS_WORKSPACE to the existing local SpotATS_ws}"
: "${ISAACLAB_ROOT:?Set ISAACLAB_ROOT}"
: "${ISAAC_PYTHON:?Set ISAAC_PYTHON to the Isaac Sim Python executable}"
site="$($ISAAC_PYTHON -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])')"
ros_root="$site/isaacsim/exts/isaacsim.ros2.bridge/humble"
export ROS_DISTRO=humble
export ROS_DOMAIN_ID="${ROS_DOMAIN_ID:-91}"
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export FASTRTPS_DEFAULT_PROFILES_FILE="$(cd "$(dirname "$0")/.." && pwd)/config/fastdds.xml"
export PYTHONPATH="$ros_root/rclpy:$SPOTATS_WORKSPACE:$ISAACLAB_ROOT"
export LD_LIBRARY_PATH="$ros_root/lib:${LD_LIBRARY_PATH:-}"
exec "$ISAAC_PYTHON" -u "$(dirname "$0")/run_unified.py" --workspace "$SPOTATS_WORKSPACE" "$@"
