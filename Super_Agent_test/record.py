"""Record the simulator's RGB topic with wall-time frame repetition and status overlay."""
import os
from pathlib import Path
import subprocess
import time

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image

OUT = Path('/out')


class Recorder(Node):
    def __init__(self):
        super().__init__('family_agent_recorder')
        self.start = None; self.previous = None; self.frames = 0
        self.encoder = subprocess.Popen(['ffmpeg', '-loglevel', 'error', '-y', '-f', 'rawvideo', '-pixel_format', 'rgb24',
            '-video_size', '640x480', '-framerate', '10', '-i', '-', '-vf',
            'drawbox=x=0:y=0:w=iw:h=72:color=black@0.75:t=fill,drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:textfile=/out/status.txt:reload=1:fontcolor=white:fontsize=19:x=12:y=12',
            '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '/out/simulation.mp4'], stdin=subprocess.PIPE)
        self.create_subscription(Image, '/vision/color/image_raw', self.frame, qos_profile_sensor_data)

    def frame(self, m):
        if (m.encoding, m.width, m.height, m.step) != ('rgb8', 640, 480, 1920): return
        now = time.monotonic()
        if self.start is None: self.start, self.previous = now, bytes(m.data)
        self.flush(now); self.previous = bytes(m.data)

    def flush(self, now):
        if self.start is None: return
        target = int((now-self.start)*10)+1
        while self.frames < target:
            self.encoder.stdin.write(self.previous); self.frames += 1


def main():
    rclpy.init(); n = Recorder(); started = time.monotonic(); done_seen = None
    try:
        while time.monotonic() - started < 180:
            rclpy.spin_once(n, timeout_sec=.1)
            if (OUT / 'record.stop').exists():
                done_seen = done_seen or time.monotonic()
                if time.monotonic() - done_seen > 3: break
    finally:
        n.flush(time.monotonic()); n.encoder.stdin.close(); code = n.encoder.wait(timeout=30)
        n.destroy_node(); rclpy.shutdown()
    if code or n.frames < 5: raise SystemExit('recording failed')


if __name__ == '__main__': main()
