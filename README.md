# challenge2ros2

TurtleBot SLAM exploration marking & evaluation — **ROS 2** edition.

## Build

```bash
cd ~/ros2_ws
colcon build --packages-select challenge2ros2
source install/setup.bash
```

## Run

```bash
ros2 launch challenge2ros2 challenge2.launch.py group:=<group> world:=<world>
```

## Test

```bash
colcon test --packages-select challenge2ros2 --event-handlers console_direct+
colcon test-result --verbose
```

## Notes

- The `turtlebot_explorer` package must be available as a ROS 2 package in the
  same workspace.
- The marking node calls the `/dynamic_map` service (`nav_msgs/srv/GetMap`)
  which is typically served by SLAM Toolbox.
- Ground-truth map serving uses `nav2_map_server` (a Nav2 lifecycle node).
