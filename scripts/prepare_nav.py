"""Derive deployment settings from the installed Nav2 example (Apache-2.0)."""
from pathlib import Path
import yaml

root=Path(__file__).resolve().parents[1]
source=Path('/opt/ros/humble/share/nav2_bringup/params/nav2_params.yaml')
data=yaml.safe_load(source.read_text())
def visit(obj):
    if isinstance(obj,dict):
        for k,v in obj.items():
            if k=='use_sim_time':obj[k]=True
            elif k in ('robot_base_frame','base_frame_id'):obj[k]='body'
            elif k in ('global_frame','global_frame_id'):obj[k]='odom'
            else:visit(v)
    elif isinstance(obj,list):
        for v in obj:visit(v)
visit(data)
bt=data['bt_navigator']['ros__parameters']
bt.update(default_server_timeout=10000,wait_for_service_timeout=10000,default_nav_to_pose_bt_xml='/opt/ros/humble/share/nav2_bt_navigator/behavior_trees/navigate_w_replanning_time.xml')
ctrl=data['controller_server']['ros__parameters']
ctrl['controller_frequency']=10.0
ctrl['progress_checker']['movement_time_allowance']=60.0
ctrl['general_goal_checker'].update(xy_goal_tolerance=.3,yaw_goal_tolerance=.5)
ctrl['FollowPath']={'plugin':'nav2_regulated_pure_pursuit_controller::RegulatedPurePursuitController','desired_linear_vel':.3,'lookahead_dist':.5,'use_rotate_to_heading':True,'allow_reversing':False,'rotate_to_heading_angular_vel':.3,'use_collision_detection':True,'transform_tolerance':.5}
for key in ('local_costmap','global_costmap'):
    d=data[key][key]['ros__parameters']
    d.update(global_frame='odom',robot_base_frame='body',rolling_window=True,width=24 if key=='global_costmap' else 6,height=24 if key=='global_costmap' else 6,resolution=.05,track_unknown_space=False,plugins=['obstacle_layer','inflation_layer'],footprint='[[0.65,0.42],[0.65,-0.42],[-0.65,-0.42],[-0.65,0.42]]',transform_tolerance=.5)
    d['obstacle_layer']={'plugin':'nav2_costmap_2d::ObstacleLayer','enabled':True,'observation_sources':'scan','scan':{'topic':'/scan','data_type':'LaserScan','marking':True,'clearing':True,'max_obstacle_height':2.5,'obstacle_max_range':20.0,'raytrace_max_range':20.0}}
    d['inflation_layer']={'plugin':'nav2_costmap_2d::InflationLayer','inflation_radius':.65,'cost_scaling_factor':3.0}
data['velocity_smoother']['ros__parameters'].update(max_velocity=[.3,0.,.3],min_velocity=[-.1,0.,-.3],max_accel=[.3,0.,.5],max_decel=[-.3,0.,-.5])
(root/'config/nav2.yaml').write_text(yaml.safe_dump(data,sort_keys=False))
print(root/'config/nav2.yaml')
