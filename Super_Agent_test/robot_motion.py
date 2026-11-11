"""Simulation-only bounded motion skill, executed by the Super-agent Worker."""
import json
import math
from pathlib import Path
import time

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped, Twist

OUT = Path('/out')
GOAL = (-1.1, -1.1)


def status(text):
    temporary = OUT / 'status.tmp'
    temporary.write_text('DEEPSEEK SUPER-AGENT | SIMULATION\n' + text, encoding='utf-8')
    temporary.replace(OUT / 'status.txt')


class Skill(Node):
    def __init__(self):
        super().__init__('family_agent_simulation_skill')
        self.pose = None
        self.last_pose = 0.0
        self.pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.create_subscription(PoseStamped, '/motion/pose', self.on_pose, 10)

    def on_pose(self, m):
        p, q = m.pose.position, m.pose.orientation
        self.pose = (p.x, p.y, math.atan2(2*(q.w*q.z + q.x*q.y), 1-2*(q.y*q.y+q.z*q.z)))
        self.last_pose = time.monotonic()


def main():
    rclpy.init(); node = Skill(); started = time.monotonic()
    result = {'success': False, 'source': 'simulation'}
    try:
        status('WORKER: running bounded ROS motion skill')
        while time.monotonic() - started < 45:
            rclpy.spin_once(node, timeout_sec=0.1)
            if node.pose is None: continue
            if time.monotonic() - node.last_pose > 1: raise RuntimeError('pose feedback stale')
            x, y, yaw = node.pose
            dx, dy = GOAL[0] - x, GOAL[1] - y
            distance = math.hypot(dx, dy)
            if distance < .09:
                result.update(success=True, goal=list(GOAL), pose=[x, y], distance_m=distance)
                status('WORKER: reached activity point | Awaiting task report')
                break
            error = math.atan2(math.sin(math.atan2(dy, dx)-yaw), math.cos(math.atan2(dy, dx)-yaw))
            cmd = Twist(); cmd.angular.z = max(-.7, min(.7, 1.8*error))
            if abs(error) < .18: cmd.linear.x = min(.16, max(.05, distance*.6))
            node.pub.publish(cmd)
        if not result['success']: result['error'] = 'timeout'
    except Exception as exc:
        result['error'] = str(exc)
    finally:
        node.pub.publish(Twist())
        (OUT / 'motion_result.json').write_text(json.dumps(result, indent=2))
        node.destroy_node(); rclpy.shutdown()
    print(json.dumps(result), flush=True)
    if not result['success']: raise SystemExit(1)


if __name__ == '__main__': main()
