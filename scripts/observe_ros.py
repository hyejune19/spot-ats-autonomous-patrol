"""Record real ROS topics and request a bounded Nav2 demonstration goal."""
import argparse
import json
from pathlib import Path
import time
import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node
from nav2_msgs.action import NavigateToPose
from nav_msgs.msg import Odometry,Path as NavPath
from sensor_msgs.msg import LaserScan,PointCloud2,Image,JointState
from geometry_msgs.msg import Twist

p=argparse.ArgumentParser()
p.add_argument('--output',required=True)
p.add_argument('--seconds',type=float,default=180)
p.add_argument('--goal',action='store_true')
p.add_argument('--plan',help='Validated LLM plan record JSON; first move_to is executed')
a=p.parse_args()
a.goal = a.goal or bool(a.plan)
target=[2.0,.5]
if a.plan:
    plan_records=json.loads(Path(a.plan).read_text())
    steps=plan_records[0]['plan']['steps']
    if any(s['task'] not in ('move_to','report_and_wait') for s in steps):raise ValueError('This bounded runner accepts movement/report only')
    moves=[s for s in steps if s['task']=='move_to']
    if len(moves)!=1:raise ValueError('Exactly one move_to is required')
    g=moves[0]['params']['goal'];target=[float(g['x']),float(g['y'])]
    if not all(-3<=v<=3 for v in target):raise ValueError('Goal outside demonstration bounds')
print('RECORDER_INIT',flush=True)
rclpy.init()
n=Node('spot_ats_evidence_recorder')
print('RECORDER_READY',flush=True)
records={'topics':{},'odometry':[],'paths':[],'commands':[],'goal':None}
def save(topic,msg):
    records['topics'][topic]=records['topics'].get(topic,0)+1
    if topic=='/odom':
        q=msg.pose.pose.position
        records['odometry'].append([msg.header.stamp.sec+msg.header.stamp.nanosec/1e9,q.x,q.y,q.z])
    if topic=='/plan':records['paths'].append([[v.pose.position.x,v.pose.position.y] for v in msg.poses])
    if topic=='/cmd_vel':records['commands'].append([msg.linear.x,msg.angular.z])
for topic,typ in [('/odom',Odometry),('/scan',LaserScan),('/point_cloud',PointCloud2),('/yolo/image_raw',Image),('/depth',Image),('/spot_joint_states',JointState),('/plan',NavPath),('/cmd_vel',Twist)]:
    n.create_subscription(typ,topic,lambda msg,t=topic:save(t,msg),10)
client=ActionClient(n,NavigateToPose,'navigate_to_pose')
start=time.monotonic()
last_status=start
future=None
result_future=None
while time.monotonic()-start<a.seconds:
    rclpy.spin_once(n,timeout_sec=.1)
    if time.monotonic()-last_status>10:
        print('OBSERVED',records['topics'],'server',client.server_is_ready(),flush=True)
        last_status=time.monotonic()
        Path(a.output).write_text(json.dumps(records,indent=2))
    if a.goal and future is None and records['odometry'] and client.server_is_ready():
        goal=NavigateToPose.Goal()
        goal.pose.header.frame_id='odom'
        goal.pose.pose.position.x=target[0]
        goal.pose.pose.position.y=target[1]
        goal.pose.pose.orientation.w=1.0
        future=client.send_goal_async(goal)
        records['goal']={'target':target,'frame':'odom','source':'llm_plan' if a.plan else 'fixed_demo'}
    if future is not None and future.done() and result_future is None:
        handle=future.result()
        records['goal']['accepted']=handle.accepted
        if handle.accepted:result_future=handle.get_result_async()
    if result_future is not None and result_future.done():
        records['goal']['status']=result_future.result().status
        break
records['nodes']=n.get_node_names()
Path(a.output).write_text(json.dumps(records,indent=2))
print(json.dumps({'topics':records['topics'],'goal':records['goal']}))
n.destroy_node()
rclpy.shutdown()
