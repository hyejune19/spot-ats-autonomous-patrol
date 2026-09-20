"""Independent integration entry point; existing licensed assets remain local."""
import argparse
import asyncio
import json
import math
import os
from pathlib import Path
import sys
import time
import threading
import traceback

from isaaclab.app import AppLauncher

p = argparse.ArgumentParser()
p.add_argument('--workspace', required=True)
p.add_argument('--output', required=True)
p.add_argument('--duration', type=float, default=12)
p.add_argument('--mode', choices=['walk','ats','perception','ros'], default='walk')
p.add_argument('--capture', action='store_true')
p.add_argument('--rgbd', action='store_true')
AppLauncher.add_app_launcher_args(p)
a = p.parse_args()
a.enable_cameras = a.capture or a.rgbd
app = AppLauncher(a).app
sys.path.insert(0, str(Path(a.workspace).resolve()))
import gymnasium as gym
import numpy as np
import torch
import isaaclab_tasks
import training.spot_ats_project_task
from isaaclab_tasks.utils import parse_env_cfg
from runtime.command_safety import VelocitySafetyFilter
from runtime.analytic_lidar import AnalyticWarehouseLidar
from runtime.ros_interface import RuntimeRosInterface
from geometry_msgs.msg import Twist
from PIL import Image

out = Path(a.output)
out.mkdir(parents=True, exist_ok=True)
for sub in ('overview','rgb','depth'):
    (out/sub).mkdir(exist_ok=True)
ros = RuntimeRosInterface()
ats_velocity = [0., 0.]
last_cmd = [time.monotonic()]
def on_ats(msg):
    ats_velocity[:] = [msg.angular.z, msg.angular.y]
    last_cmd[0] = time.monotonic()
ros.node.create_subscription(Twist, '/ats_twist', on_ats, 10)
task = 'Isaac-Velocity-Flat-Spot-ATS-Project-Lidar-Runtime-v0'
cfg = parse_env_cfg(task, device=a.device, num_envs=1)
cfg.seed = 42
cfg.commands.base_velocity.debug_vis = False
if a.mode == 'perception':
    cfg.scene.person.init_state.pos = (3.0, 0.0, 0.0)
env = gym.make(task, cfg=cfg)
base = env.unwrapped
obs, _ = env.reset()
import omni.usd
from pxr import UsdGeom
visuals=omni.usd.get_context().get_stage().GetPrimAtPath('/Visuals')
if visuals.IsValid():UsdGeom.Imageable(visuals).MakeInvisible()
robot = base.scene['robot']
policy = torch.jit.load(str(Path(a.workspace)/'ATS_IsaacSim/Main/ATS_Enviroment/spot_policy.pt'),map_location=base.device).eval()
joint_ids = [robot.joint_names.index(n) for n in ('joint1','joint2')]
ats_target = robot.data.joint_pos[:,joint_ids].clone()
limits = robot.data.soft_joint_pos_limits[:,joint_ids,:]
command = base.command_manager._terms['base_velocity']
safety = VelocitySafetyFilter(base.device, base.step_dt)
lidar = AnalyticWarehouseLidar(robot)
camera = None
viewport = None
if a.rgbd:
    from isaacsim.core.utils.extensions import enable_extension
    enable_extension('isaacsim.sensors.camera')
    from runtime.replicator_camera import RuntimeReplicatorCamera
    camera = RuntimeReplicatorCamera(robot, resolution=(640,480))
    camera.camera.set_focal_length(10.5)
    camera.camera.set_horizontal_aperture(20.955)
if a.capture:
    from isaacsim.core.utils.extensions import enable_extension
    enable_extension('isaacsim.sensors.camera')
    from isaacsim.sensors.camera import Camera
    from scipy.spatial.transform import Rotation
    viewport = Camera(prim_path='/World/DocumentationCamera',resolution=(1280,720),frequency=10)
    viewport.initialize(attach_rgb_annotator=True)
    viewport.set_focal_length(18.0)
    viewport.set_horizontal_aperture(20.955)
    def aim(eye,target):
        eye=np.asarray(eye);forward=np.asarray(target)-eye;forward/=np.linalg.norm(forward)
        left=np.cross([0.,0.,1.],forward);left/=np.linalg.norm(left)
        up=np.cross(forward,left)
        q=Rotation.from_matrix(np.stack([forward,left,up],axis=1)).as_quat()
        viewport.set_world_pose(eye,np.array([q[3],*q[:3]]),camera_axes='world')
    aim((3.4,3.4,2.6),(0.,0.,.65))
    for _ in range(12):
        base.sim.render()
records=[]
frames=0
dt=base.step_dt
print('UNIFIED_READY', flush=True)
try:
    with torch.inference_mode():
        for i in range(round(a.duration/dt)):
            t=i*dt
            ros.spin()
            requested=ros.command if a.mode=='ros' else ([.3,0.,0.] if a.mode=='walk' else [0.,0.,0.])
            cmd=safety.filter(torch.tensor([requested],device=base.device))
            command.is_standing_env[:]=False
            command.vel_command_b[:]=cmd
            if a.mode=='ats':
                ats_target[0,0]=.65*math.sin(t*.7)
                ats_target[0,1]=-.25*(1-math.cos(t*.9))
            elif time.monotonic()-last_cmd[0]<.5:
                ats_target += torch.tensor([ats_velocity],device=base.device).clamp(-.6,.6)*dt
            ats_target=torch.max(torch.min(ats_target,limits[:,:,1]),limits[:,:,0])
            robot.set_joint_position_target(ats_target,joint_ids=joint_ids)
            if camera:
                camera.update_pose()
            obs,_,_,_,_=env.step(policy(obs['policy']))
            command.is_standing_env[:]=False
            command.vel_command_b[:]=cmd
            ros.publish((i+1)*dt,robot,robot.joint_names)
            if i%5==0:
                points2,points3=lidar.scan()
                ros.publish_lidar_points((i+1)*dt,points2,points3)
                pos=robot.data.root_pos_w[0].cpu().tolist()
                tilt=float(torch.acos((-robot.data.projected_gravity_b[0,2]).clamp(-1,1)))
                safety.update_attitude(tilt)
                records.append(dict(t=(i+1)*dt,position=pos,quaternion=robot.data.root_quat_w[0].cpu().tolist(),tilt=tilt,joints=robot.data.joint_pos[0].cpu().tolist(),command=cmd[0].cpu().tolist()))
                np.savez_compressed(out/'latest_scan.npz',points2=points2.cpu().numpy(),points3=points3.cpu().numpy())
                if viewport:
                    aim((pos[0]+3.4,pos[1]+3.4,2.6),(pos[0],pos[1],.65))
                    for _ in range(3):base.sim.render()
                    frame_path=out/'overview'/f'{frames:05d}.png'
                    rgba=np.asarray(viewport.get_rgba())
                    if rgba.ndim!=3:raise RuntimeError('Overview camera is not ready')
                    Image.fromarray(rgba[:,:,:3].astype(np.uint8)).save(frame_path)
                if camera:
                    frame=camera.read()
                    if frame is not None:
                        rgb,depth=frame
                        ros.publish_camera_arrays((i+1)*dt,rgb,depth)
                        Image.fromarray(rgb).save(out/'rgb'/f'{frames:05d}.png')
                        np.save(out/'depth'/f'{frames:05d}.npy',depth)
                frames+=1
            if i%100==0:
                print(f'UNIFIED_STEP {i} / {round(a.duration/dt)}',flush=True)
    summary={'mode':a.mode,'sim_seconds':a.duration,'step_dt':dt,'joint_names':robot.joint_names,'body_names':robot.body_names,'ats_limits_rad':limits.cpu().tolist(),'samples':records,'scan_messages':ros.lidar_messages,'source':'actual Isaac Sim execution, seed 42'}
    (out/'telemetry.json').write_text(json.dumps(summary,indent=2))
except BaseException:
    traceback.print_exc()
    raise
finally:
    if camera:
        camera.close()
    ros.close()
    env.close()
    # Kit camera extensions can stall on shutdown after files have been flushed.
    shutdown_guard=threading.Timer(10,lambda:os._exit(0 if (out/'telemetry.json').exists() else 1))
    shutdown_guard.daemon=True
    shutdown_guard.start()
    app.close()
