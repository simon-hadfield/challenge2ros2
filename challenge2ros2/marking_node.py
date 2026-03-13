#!/usr/bin/env python3
"""Marking node – evaluates SLAM exploration coverage over time."""

import os
import threading
import time

from geometry_msgs.msg import PoseStamped
from nav_msgs.srv import GetMap
import numpy as np
from PIL import Image
import rclpy
from rclpy.node import Node


def get_map_image(map_resp):
    """Convert a GetMap response into a grayscale numpy image."""
    grid = np.array(map_resp.map.data).reshape(
        (map_resp.map.info.height, map_resp.map.info.width))
    grid = grid.copy()
    grid[grid == -1] = 128
    grid[grid == 0] = 255
    grid[grid == 100] = 0
    return grid


class Marker(Node):
    """Periodically polls the SLAM map and records exploration coverage."""

    def __init__(self):
        super().__init__('marker')

        # --- parameters ------------------------------------------------
        self.declare_parameter('group', -1)
        self.declare_parameter('world', '')
        self.declare_parameter('savepath', '~/challenge2')
        self.declare_parameter('duration', 0)

        self.group = self.get_parameter('group').get_parameter_value().integer_value
        if self.group < 0:
            self.get_logger().error("You haven't set the group!")
            raise SystemExit(1)

        self.world = self.get_parameter('world').get_parameter_value().string_value
        if not self.world:
            self.get_logger().error("You haven't set the world!")
            raise SystemExit(1)

        self.save_path = os.path.expanduser(
            self.get_parameter('savepath').get_parameter_value().string_value)
        self.duration = (
            self.get_parameter('duration').get_parameter_value().integer_value)

        os.makedirs(self.save_path, exist_ok=True)

        self.save_file = '{}/{}_{}_log.txt'.format(
            self.save_path, self.group, self.world)
        self.save_plot = '{}/{}_{}_plot.png'.format(
            self.save_path, self.group, self.world)
        self.save_map = '{}/{}_{}_est.jpg'.format(
            self.save_path, self.group, self.world)
        self.get_logger().info('Saving to {}'.format(self.save_file))

        # --- ROS interfaces --------------------------------------------
        # Service client – SLAM toolbox exposes /slam_toolbox/dynamic_map (GetMap)
        self.get_map_cli = self.create_client(GetMap, '/slam_toolbox/dynamic_map')

        # Nav2 simple-goal topic (replaces ROS1 /move_base_simple/goal)
        self.goal_pub = self.create_publisher(PoseStamped, '/goal_pose', 1)

        # --- state ------------------------------------------------------
        self.explored_cells = 0
        self.latest_map_msg = None
        self.curr_map = None
        self.score = [0.0]
        self.times = [0.0]
        self.start_time = None

    # -----------------------------------------------------------------
    def process_map(self, map_msg):
        """Count explored cells and return the raw score."""
        self.get_logger().info('Processing Map...')
        grid = np.array(map_msg.data)
        self.explored_cells = self._get_explored_cells(grid)
        self.get_logger().info('Explored Cells %d' % self.explored_cells)
        score = float(self.explored_cells)
        return score

    @staticmethod
    def _get_explored_cells(gridmap):
        """Return the number of cells with a known occupancy value."""
        return int(np.count_nonzero(gridmap > -1))

    def update_map(self):
        """Fetch the latest map via the GetMap service."""
        self.get_logger().info('Updating Map...')
        try:
            future = self.get_map_cli.call_async(GetMap.Request())
            # Spinning happens in a background thread; just poll the future.
            deadline = time.time() + 5.0
            while not future.done() and time.time() < deadline:
                time.sleep(0.01)
            if not future.done():
                self.get_logger().warn('Service call timed out')
                return False

            map_resp = future.result()
            if map_resp is None:
                self.get_logger().warn('Service call returned None')
                return False

            # Default SLAM map is 64x64 before any real data arrives
            if map_resp.map.info.width <= 64:
                return False

            self.latest_map_msg = map_resp.map
            self.get_logger().info('Map Updated')
            self.curr_map = get_map_image(map_resp)

        except Exception as e:
            self.get_logger().warn('Service call failed to get map: %s' % e)
            return False

        return True

    # -----------------------------------------------------------------
    def run(self):
        """Blocking polling loop – call from the main thread."""
        self.get_logger().info('Waiting for /dynamic_map service...')
        while not self.get_map_cli.wait_for_service(timeout_sec=1.0):
            if not rclpy.ok():
                return
            self.get_logger().info('Still waiting for /dynamic_map service...')

        self.start_time = self.get_clock().now()
        period = 0.5  # 2 Hz

        while rclpy.ok():
            elapsed_sec = (
                (self.get_clock().now() - self.start_time).nanoseconds / 1e9)
            if elapsed_sec >= float(self.duration):
                break

            self.get_logger().info('New Score Estimate...')
            if self.update_map():
                score = 100.0 * self.process_map(self.latest_map_msg)
                now_sec = (
                    (self.get_clock().now() - self.start_time).nanoseconds
                    / 1e9)
                self.times.append(now_sec)
                self.score.append(score)
                self.get_logger().warn('SCORE %f' % self.score[-1])

            time.sleep(period)

        elapsed_sec = (
            (self.get_clock().now() - self.start_time).nanoseconds / 1e9)
        self.get_logger().warn(
            'Terminating after %f seconds with a score of: %0.2f%%'
            % (elapsed_sec, self.score[-1]))

        # --- persist results -------------------------------------------
        if self.curr_map is not None:
            Image.fromarray(np.uint8(self.curr_map * 255)).save(self.save_map)

        with open(self.save_file, 'w') as f:
            f.write('{:0.3f}'.format(self.score[-1]))

        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt  # noqa: E402
        plt.plot(self.times, self.score)
        plt.title('Group {}, World {}'.format(self.group, self.world))
        plt.xlabel('Time (s)')
        plt.ylabel('Exploration (%)')
        plt.savefig(self.save_plot)


def main(args=None):
    """Entry point for the marking_node executable."""
    rclpy.init(args=args)
    marker = Marker()

    # Spin in a background thread so service futures resolve.
    spin_thread = threading.Thread(target=rclpy.spin, args=(marker,),
                                   daemon=True)
    spin_thread.start()

    try:
        marker.run()
    except KeyboardInterrupt:
        pass
    finally:
        marker.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
