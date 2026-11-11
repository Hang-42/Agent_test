import cv2
import mujoco
import numpy as np

m=mujoco.MjModel.from_xml_path('/work/robot/simulation/generated/mujoco__home_with_robot.xml')
d=mujoco.MjData(m); mujoco.mj_forward(m,d); renderer=mujoco.Renderer(m,height=240,width=360)
frames=[]
for angle in (0,45,90,135,180,225,270,315):
 c=mujoco.MjvCamera(); c.lookat[:]=[-1.1,-1.7,.6]; c.distance=2.2; c.elevation=-28; c.azimuth=angle
 renderer.update_scene(d,camera=c); im=cv2.cvtColor(renderer.render().copy(),cv2.COLOR_RGB2BGR)
 cv2.putText(im,str(angle),(10,25),cv2.FONT_HERSHEY_SIMPLEX,.7,(0,0,255),2); frames.append(im)
cv2.imwrite('/out/camera_survey.jpg',np.vstack([np.hstack(frames[:4]),np.hstack(frames[4:])]))
renderer.close()
