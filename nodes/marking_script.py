#!/usr/bin/env python
from __future__ import print_function

import rospy
import rospkg
import numpy as np
from nav_msgs.msg import OccupancyGrid
from geometry_msgs.msg import PoseStamped
from nav_msgs.srv import GetMap, GetMapResponse

import os

class Marker:

    def __init__(self):

        self.group_name = rospy.get_param('~group_name')
        print("Group: {}".format(self.group_name))

        pid_path = rospy.get_param('~pid_path')
        self.kill_cmd = "kill -INT `cat {}`".format(pid_path)
        print("Kill Command: {}".format(self.kill_cmd))

        rospack = rospkg.RosPack()
        package_path = rospack.get_path('turtlebot_explorer')
        file_path = "{}/{}_scores.txt".format(package_path,self.group_name)
        self.file_out = open(file_path, "w+")

        # Define a Service for Map
        rospy.wait_for_service('/dynamic_map')
        self.get_map_srv = rospy.ServiceProxy('/dynamic_map', GetMap)

        # Define a Timer to send goals
        self.timeout = rospy.get_param('~timeout')
        rospy.Timer(rospy.Duration(self.timeout), self.timer_cb)

        #Defined Explored Cells
        self.explored_cells = 0

        self.latest_map_msg = None

        self.total_cells = self.get_gt_map()
        rospy.loginfo("Total Cells %i", self.total_cells)

        self.explore_curve = []

    def write_scores(self,scores):
        for s in scores:
            self.file_out.write("{}\n".format(s))

    def timer_cb(self, event):
        self.write_scores(self.explore_curve)
        rospy.logwarn("Killing! {}".format(self.kill_cmd))
        #os.system("source /opt/ros/kinetic/setup.bash && rosrun map_server map_saver -f {}_map".format(self.group_name))
        os.system(self.kill_cmd)
        #self.file_out.close()

    def get_gt_map(self):
        rospy.wait_for_service('/static_map')
        gt_map_srv = rospy.ServiceProxy('/static_map', GetMap)

        while True:
            try:
                map_resp = gt_map_srv()
                assert isinstance(map_resp, GetMapResponse)

                if map_resp.map.info.width <= 64:  # Default size of map before any input (64x64)
                    continue

                map_msg = map_resp.map
                map = np.array(map_msg.data)
                return self.get_explored_cells(map_msg.info.height, map, map_msg.info.width)


            except rospy.ServiceException, e:
                rospy.logwarn("Service call failed to get map: %s" % e)
                exit(0)

    def process_map(self, map_msg):
        rospy.loginfo("Processing Map...")

        # Get Map Metadata
        width = map_msg.info.width
        height = map_msg.info.height
        map = np.array(map_msg.data)

        # Pick Goal and Crate Msg
        self.explored_cells = self.get_explored_cells(height, map, width)
        rospy.loginfo("Explored Cells %i", self.explored_cells)

        score = float(self.explored_cells) / float(self.total_cells)
        self.explore_curve.append(score)
        print(score)

        return score


    # Overload get_valid_cells to return explored cells
    def get_explored_cells(self, height, gridmap, width):

        # Get Number of Explored Cells
        cells_explored = np.count_nonzero(gridmap > -1)
        return cells_explored

    def update_map(self):
        rospy.loginfo("Updating Map...")
        try:
            map_resp = self.get_map_srv()
            assert isinstance(map_resp, GetMapResponse)

            if map_resp.map.info.width <= 64:  #Default size of map before any input (64x64)
                return False

            self.latest_map_msg = map_resp.map
            rospy.loginfo("Map Updated")

        except rospy.ServiceException, e:
            rospy.logwarn("Service call failed to get map: %s" % e)
            return False

        return True

    def loop(self):
        rate = rospy.Rate(1.0)

        while not rospy.is_shutdown():
            rospy.loginfo("New Score Estimate...")

            if self.update_map():
                score = self.process_map(self.latest_map_msg)
                rospy.loginfo("SCORE %f", score)

            rate.sleep()


if __name__ == '__main__':
    rospy.init_node('marker',anonymous=True)
    marker = Marker()
    marker.loop()
