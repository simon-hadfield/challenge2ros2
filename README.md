# TO RUN, USE the following Syntax

roslaunch turtlebot_explorer_marker marking_sim.launch --pid=/tmp/roslaunch.pid group:=<group_name> start:=<loc> rep:=<rep_num>

NOTE:
You MUST use the `--pid=/tmp/roslaunch.pid` flag, as this is what is used to kill the launch file.
