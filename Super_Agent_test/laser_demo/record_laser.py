"""Record live RGB-D simulation, pose-reconstructed observer view and actual event log."""
import json
import math
import os
from pathlib import Path
import subprocess
import time
import cv2
import mujoco
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image, JointState
from geometry_msgs.msg import PoseStamped

OUT = Path('/out')

class Recorder(Node):
    def __init__(self):
        super().__init__('family_rich_recorder')
        self.model = mujoco.MjModel.from_xml_path('/work/robot/simulation/generated/mujoco__home_with_robot.xml')
        self.data = mujoco.MjData(self.model)
        self.free = self.model.joint('robot_freejoint').qposadr[0]
        self.renderer = mujoco.Renderer(self.model, height=320, width=560)
        self.cam = mujoco.MjvCamera(); self.cam.distance = 2.2; self.cam.azimuth = 315; self.cam.elevation = -28
        self.camera_id = self.model.camera('robot_rgbd_camera').id
        self.camera_body = self.model.body('robot_gimbal_pitch').id
        self.rgb = None; self.pose = None; self.started = time.monotonic(); self.next_frame = self.started; self.frames = 0; self.video_start = None
        self.encoder = subprocess.Popen(['ffmpeg', '-loglevel', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
            '-s', '1600x900', '-r', '6', '-i', '-', '-vf',
            'drawtext=fontfile=/fonts/cjk.ttc:textfile=/out/terminal.txt:reload=1:fontcolor=white:fontsize=23:line_spacing=15:x=630:y=108',
            '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '21',
            '-pix_fmt', 'yuv420p', '/out/'+os.environ.get('RECORD_NAME','laser_full.mp4')], stdin=subprocess.PIPE)
        (OUT/'terminal.txt').write_text('等待仿真事件...',encoding='utf-8')
        self.create_subscription(Image, '/vision/color/image_raw', self.on_image, qos_profile_sensor_data)
        self.create_subscription(PoseStamped, '/motion/pose', self.on_pose, 10)
        self.create_subscription(JointState, '/joint_states', self.on_joints, 10)

    def on_image(self, msg):
        if msg.encoding == 'rgb8' and msg.step >= msg.width*3:
            a = np.frombuffer(msg.data, np.uint8).reshape(msg.height, msg.step)[:, :msg.width*3]
            self.rgb = a.reshape(msg.height, msg.width, 3).copy()

    def on_pose(self, msg):
        p,q = msg.pose.position, msg.pose.orientation
        self.pose = (p.x,p.y,p.z,q.w,q.x,q.y,q.z)

    def on_joints(self, msg):
        for name, value in zip(msg.name, msg.position):
            try: self.data.qpos[self.model.joint(name).qposadr[0]] = value
            except KeyError: pass

    def draw_frame(self):
        if self.pose is None or self.rgb is None: return None
        self.data.qpos[self.free:self.free+7] = self.pose
        mujoco.mj_forward(self.model, self.data)
        self.cam.lookat[:] = [self.pose[0], self.pose[1], 0.6]
        self.renderer.update_scene(self.data, camera=self.cam)
        dot=None
        try:
            active=json.loads((OUT/'laser.json').read_text()).get('active',False)
        except (OSError,ValueError): active=False
        if active:
            rotation=self.data.cam_xmat[self.camera_id].reshape(3,3)
            forward=-rotation[:,2]; origin=self.data.cam_xpos[self.camera_id]+rotation[:,1]*.06+forward*.15
            hit_id=np.array([-1],dtype=np.int32)
            distance=mujoco.mj_ray(self.model,self.data,origin,forward,None,True,self.camera_body,hit_id)
            if distance>0:
                dot=origin+forward*distance
                scene=self.renderer.scene
                if scene.ngeom<scene.maxgeom:
                    geom=scene.geoms[scene.ngeom]
                    mujoco.mjv_initGeom(geom,mujoco.mjtGeom.mjGEOM_CAPSULE,np.zeros(3),np.zeros(3),np.eye(3).reshape(-1),np.array([1.,.05,.05,.9],dtype=np.float32))
                    mujoco.mjv_connector(geom,mujoco.mjtGeom.mjGEOM_CAPSULE,.012,origin,dot)
                    scene.ngeom+=1
        third = self.renderer.render().copy()
        first = cv2.resize(self.rgb, (560, 320))
        if dot is not None:
            point=rotation.T@(dot-self.data.cam_xpos[self.camera_id]); z=-point[2]
            if z>0:
                f=320/(2*math.tan(math.radians(float(self.model.cam_fovy[self.camera_id]))/2))
                u=int(280+f*point[0]/z); v=int(160-f*point[1]/z)
                if 0<=u<560 and 0<=v<320: cv2.circle(first,(u,v),7,(255,35,35),-1)
        canvas = np.zeros((900,1600,3),np.uint8); canvas[:]=[16,23,34]
        canvas[88:408,24:584]=first; canvas[476:796,24:584]=third
        cv2.rectangle(canvas,(610,88),(1576,844),(8,16,25),-1)
        font=cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(canvas,'FAMILY AGENT | DEEPSEEK SUPER-AGENT', (24,36),font,.8,(238,244,255),2)
        cv2.putText(canvas,'FIRST PERSON | LIVE RGB', (24,73),font,.55,(158,213,255),1)
        cv2.putText(canvas,'OBSERVER SIDE VIEW | ROS POSE', (24,460),font,.55,(158,213,255),1)
        cv2.putText(canvas,'AGENT EVENT TERMINAL | ACTUAL MESSAGES', (610,73),font,.55,(158,213,255),1)
        cv2.putText(canvas,'Synthetic interaction | Virtual laser overlay | Preset simulation routes', (24,856),font,.5,(255,204,136),1)
        lines=[]
        for filename in ('timeline.jsonl',):
            path=OUT/filename
            if not path.exists(): continue
            for row in path.read_text(encoding='utf-8').splitlines():
                try:
                    e=json.loads(row)
                    if filename == 'timeline.jsonl': lines.append((e.get('at',0),e.get('text','')))
                    else:
                        stamp=e.get('received_at') or path.stat().st_mtime
                        lines.append((stamp,'Agent: '+str(e.get('text',''))))
                except (ValueError,TypeError): pass
        lines.sort(key=lambda x:x[0]); wrapped=[]
        for _, msg in lines[-12:]:
            for para in msg.replace('\n',' ').splitlines():
                while para:
                    cut=min(35,len(para)); wrapped.append(para[:cut]); para=para[cut:]
        temporary=OUT/'terminal.tmp'
        temporary.write_text('\n'.join(wrapped[-16:]) or '等待仿真事件...',encoding='utf-8')
        temporary.replace(OUT/'terminal.txt')
        return canvas

    def tick(self):
        now=time.monotonic()
        if now < self.next_frame: return
        frame=self.draw_frame()
        if frame is not None:
            if self.frames == 0: cv2.imwrite('/out/preview_start.jpg',cv2.cvtColor(frame,cv2.COLOR_RGB2BGR))
            if self.video_start is None: self.video_start=now
            target=int((now-self.video_start)*6)+1
            while self.frames < target:
                self.encoder.stdin.write(frame.tobytes()); self.frames += 1
            self.next_frame=now+1/6


def main():
    rclpy.init(); n=Recorder()
    try:
        while time.monotonic()-n.started<600:
            rclpy.spin_once(n,timeout_sec=.04); n.tick()
            if (OUT/'record.stop').exists():
                end=time.monotonic()+3
                while time.monotonic()<end: rclpy.spin_once(n,timeout_sec=.04); n.tick()
                break
    finally:
        n.encoder.stdin.close(); code=n.encoder.wait(timeout=45); n.renderer.close(); n.destroy_node(); rclpy.shutdown()
    if code: raise SystemExit(code)

if __name__ == '__main__': main()
