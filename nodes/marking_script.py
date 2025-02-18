#!/usr/bin/env python
from __future__ import print_function

import rospy
import numpy as np
from nav_msgs.msg import OccupancyGrid
from geometry_msgs.msg import PoseStamped
from nav_msgs.srv import GetMap, GetMapResponse
#import scipy.misc
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def get_param(name, err):
    try:
        param = rospy.get_param(name)
    except KeyError:
        rospy.logerr(err)
        rospy.signal_shutdown(err)
        exit()
    return param

def get_map_image(map_resp):
    map = np.array(map_resp.map.data).reshape((map_resp.map.info.width, map_resp.map.info.height))
    map[map == -1] = 128
    map[map == 0] = 255
    map[map == 100] = 0
    return map
    #scipy.misc.imsave("/tmp/map.jpg", map)

class Marker:

    def __init__(self):
        rospy.init_node('marker', anonymous=True)

        self.group = get_param('~group', "You haven't set the group!")
        self.world = get_param('~world', "You haven't set the world!")
        self.save_path = rospy.get_param('~savepath', "/vol/vssp/signsrc/challenge2")
        self.duration = rospy.get_param('~duration', 0)
        self.save_file = "{}/{}_{}_log.txt".format(self.save_path, self.group, self.world)
        self.save_plot = "{}/{}_{}_plot.png".format(self.save_path, self.group, self.world)
        self.save_map = "{}/{}_{}_est.jpg".format(self.save_path, self.group, self.world)
        rospy.loginfo("Saving to {}".format(self.save_file))

        # Define a Service for Map
        rospy.wait_for_service('/dynamic_map')
        self.get_map_srv = rospy.ServiceProxy('/dynamic_map', GetMap)

        # Define a Simple Goal Publisher
        self.goal_pub = rospy.Publisher("/move_base_simple/goal", PoseStamped, queue_size=1)

        #Defined Explored Cells
        self.explored_cells = 0

        self.latest_map_msg = None

        self.start_time = rospy.Time.now()
        self.current_time = rospy.Time.now()
        self.max_duration = rospy.Duration(self.duration)
        #self.score = [(self.start_time, 0.0)]
        self.score = [0.0]
        self.times = [0.0]
        self.curr_map = None


    def process_map(self, map_msg):
        rospy.loginfo("Processing Map...")
        rospy.Time.now()

        # Get Map Metadata
        width = map_msg.info.width
        height = map_msg.info.height
        map = np.array(map_msg.data)

        # Pick Goal and Crate Msg
        self.explored_cells = self.get_explored_cells(height, map, width)
        rospy.loginfo("Explored Cells %i", self.explored_cells)

        score = float(self.explored_cells)
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

            self.curr_map = get_map_image(map_resp)

        except rospy.ServiceException as e:
            rospy.logwarn("Service call failed to get map: %s" % e)
            return False

        return True

    def loop(self):
        rate = rospy.Rate(2.0)

        self.start_time = rospy.Time.now()
        self.current_time = self.start_time
        time_elapsed = self.current_time - self.start_time
        while not rospy.is_shutdown() and time_elapsed < self.max_duration:
            rospy.loginfo("New Score Estimate...")

            if self.update_map():
                score = 100*self.process_map(self.latest_map_msg)
                self.times.append(rospy.Time.now().to_sec() - self.start_time.to_sec())
                self.score.append(score)
                rospy.logwarn("SCORE %f", self.score[-1])

            rate.sleep()
            self.current_time = rospy.Time.now()
            time_elapsed = self.current_time - self.start_time
        rospy.logwarn("Terminating after %f seconds with a score of: %0.2f%%", time_elapsed.to_sec(), self.score[-1])

        #scipy.misc.imsave(self.save_map, self.curr_map)
        Image.fromarray(np.uint8(self.curr_map*255)).save(self.save_map)

        f = open(self.save_file, "w")
        f.write("{:0.3f}".format(self.score[-1]))
        # for t, s in zip(self.times, self.score):
        #     f.write("{:0.3f},{:0.3f}\n".format(t,s))
        f.close()

        plt.plot(self.times, self.score)
        plt.title("Group {}, World {}".format(self.group, self.world))
        plt.xlabel("Time (s)")
        plt.ylabel("Exploration (%)")
        plt.savefig(self.save_plot)

if __name__ == '__main__':
    marker = Marker()
    marker.loop()
