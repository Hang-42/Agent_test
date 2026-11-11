"""Simulation-only prevalidated waypoint and virtual pointing skills."""
import json
import math
import sys
import time
from pathlib import Path
import rclpy
from geometry_msgs.msg import PoseStamped, Twist
from sensor_msgs.msg import JointState
from rclpy.node import Node

OUT=Path('/out')
# World-frame demo waypoints, not transformed semantic-map coordinates.
WAYPOINTS={'activity':(-1.1,-1.2),'plant':(-1.1,0.8),'tv':(-1.1,-1.4),'home':(-1.1,-0.8)}
POINTS={'plant':(-4.45,2.25,0.60),'leaf':(-4.45,2.25,0.95),'tv':(-2.5,-2.74,1.0)}
NAMES={'activity':'活动点','plant':'植物观察点','tv':'电视观察点','home':'等待点'}

def log(s):
    with (OUT/'timeline.jsonl').open('a',encoding='utf-8') as f: f.write(json.dumps({'at':time.time(),'text':s},ensure_ascii=False)+'\n')

def laser(active, label=''):
    p=OUT/'laser.tmp'; p.write_text(json.dumps({'active':active,'label':label,'time':time.time()}),encoding='utf-8'); p.replace(OUT/'laser.json')

class Skill(Node):
    def __init__(self):
        super().__init__('family_scene_skill'); self.pose=None; self.stamp=0; self.joints={}
        self.pub=self.create_publisher(Twist,'/cmd_vel',10)
        self.gimbal=self.create_publisher(JointState,'/motion/gimbal_command',10)
        self.create_subscription(PoseStamped,'/motion/pose',self.pose_cb,10)
        self.create_subscription(JointState,'/joint_states',self.joint_cb,10)
    def pose_cb(self,m):
        p,q=m.pose.position,m.pose.orientation
        self.pose=(p.x,p.y,math.atan2(2*(q.w*q.z+q.x*q.y),1-2*(q.y*q.y+q.z*q.z))); self.stamp=time.monotonic()
    def joint_cb(self,m): self.joints.update(zip(m.name,m.position))
    def spin(self): rclpy.spin_once(self,timeout_sec=.06)
    def stop(self): self.pub.publish(Twist())

def main():
    action=sys.argv[1] if len(sys.argv)>1 else ''
    if action not in [*WAYPOINTS,*['point-'+x for x in POINTS]]: raise SystemExit('invalid simulation action')
    rclpy.init(); node=Skill(); deadline=time.monotonic()+150; result={'action':action,'success':False,'simulation':True}
    try:
        while node.pose is None and time.monotonic()<deadline: node.spin()
        if node.pose is None: raise RuntimeError('no pose')
        laser(False)
        if action in WAYPOINTS:
            tx,ty=WAYPOINTS[action]; log('移动：前往'+NAMES[action]+'（预设路线）')
            while time.monotonic()<deadline:
                node.spin()
                if time.monotonic()-node.stamp>1.2: raise RuntimeError('pose stale')
                x,y,yaw=node.pose; dx,dy=tx-x,ty-y; dist=math.hypot(dx,dy)
                if dist<.10:
                    node.stop(); result.update(success=True,distance_m=dist,pose=[x,y]); log('移动完成：'+NAMES[action]); break
                err=math.atan2(math.sin(math.atan2(dy,dx)-yaw),math.cos(math.atan2(dy,dx)-yaw))
                cmd=Twist(); cmd.angular.z=max(-.75,min(.75,1.8*err))
                if abs(err)<.18: cmd.linear.x=min(.28,max(.07,dist*.6))
                node.pub.publish(cmd)
        else:
            target=action[6:]; tx,ty,tz=POINTS[target]; x,y,yaw=node.pose
            desired=math.atan2(math.sin(math.atan2(ty-y,tx-x)-yaw),math.cos(math.atan2(ty-y,tx-x)-yaw))
            pitch=max(-.75,min(.45,math.atan2(1.2-tz,math.hypot(tx-x,ty-y))))
            log('云台：转向'+{'plant':'植物','leaf':'叶片','tv':'电视'}[target]+'的预设提示区域')
            while time.monotonic()<deadline:
                msg=JointState(); msg.name=['robot_gimbal_yaw_joint','robot_gimbal_pitch_joint']; msg.position=[desired,pitch]; node.gimbal.publish(msg); node.spin()
                yv=node.joints.get(msg.name[0]); pv=node.joints.get(msg.name[1])
                if yv is not None and pv is not None and abs(yv-desired)<.08 and abs(pv-pitch)<.08:
                    laser(True,target); log('虚拟激光：开启（仿真提示）'); end=time.monotonic()+4
                    while time.monotonic()<end: node.spin()
                    laser(False); log('虚拟激光：关闭'); result.update(success=True,yaw=yv,pitch=pv,target=target); break
        if not result['success']: result['error']='timeout'
    except Exception as e: result['error']=str(e)
    finally:
        node.stop(); laser(False)
        (OUT/('skill_'+action+'.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        node.destroy_node(); rclpy.shutdown()
    print(json.dumps(result),flush=True)
    if not result['success']: raise SystemExit(1)

if __name__=='__main__': main()
