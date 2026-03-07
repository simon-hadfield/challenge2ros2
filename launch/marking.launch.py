"""Launch explorer simulation with ground-truth map and marking script."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    explorer_share = FindPackageShare('turtlebot_explorer')

    return LaunchDescription([
        # ---------- arguments ------------------------------------------
        DeclareLaunchArgument('group', description='Group name / number'),

        # ---------- simulated explorer (external package) --------------
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([
                explorer_share,
                '/launch/turtlebot_explorer_sim.launch.py',
            ]),
        ),

        # ---------- ground-truth map server (Nav2 lifecycle node) ------
        Node(
            package='nav2_map_server',
            executable='map_server',
            name='map_server_gt',
            output='screen',
            parameters=[{
                'yaml_filename': [
                    explorer_share, '/maps/explore_map.yaml',
                ],
            }],
            remappings=[('map', 'map_gt')],
        ),

        # Lifecycle manager – auto-activates map_server_gt
        Node(
            package='nav2_lifecycle_manager',
            executable='lifecycle_manager',
            name='lifecycle_manager_map_server',
            output='screen',
            parameters=[{
                'autostart': True,
                'node_names': ['map_server_gt'],
            }],
        ),

        # ---------- marking script from turtlebot_explorer -------------
        Node(
            package='turtlebot_explorer',
            executable='marking_script',
            name='marking_script',
            output='screen',
            parameters=[{
                'pid_path': '/tmp/roslaunch.pid',
                'group_name': LaunchConfiguration('group'),
                'timeout': 10,
            }],
        ),
    ])
