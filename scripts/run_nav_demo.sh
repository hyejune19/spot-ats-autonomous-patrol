#!/usr/bin/env bash
set -eo pipefail
base="$(cd "$(dirname "$0")/.." && pwd)"
evidence="$base/../evidence"
source /opt/ros/humble/setup.bash
export ROS_DOMAIN_ID="${ROS_DOMAIN_ID:-91}"
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export FASTRTPS_DEFAULT_PROFILES_FILE="$base/config/fastdds.xml"
export ROS_LOG_DIR="$evidence/ros_logs"
mkdir -p "$ROS_LOG_DIR"
/usr/bin/python3 "$base/scripts/prepare_nav.py"
pids=()
cleanup() { for pid in "${pids[@]}"; do kill -TERM -- "-$pid" 2>/dev/null || true; done; }
trap cleanup EXIT INT TERM
setsid ros2 launch nav2_bringup navigation_launch.py use_sim_time:=true use_composition:=False params_file:="$base/config/nav2.yaml" > "$evidence/nav2.log" 2>&1 &
pids+=("$!")
setsid rviz2 -d "$base/config/spot_ats.rviz" > "$evidence/rviz.log" 2>&1 &
pids+=("$!")
/usr/bin/python3 -u "$base/scripts/observe_ros.py" --goal --seconds 300 --output "$evidence/nav_ros.json"
