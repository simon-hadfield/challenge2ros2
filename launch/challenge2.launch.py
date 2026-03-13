"""Launch the marking node together with the turtlebot_explorer stack."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, Shutdown
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    return LaunchDescription([
        # ---------- arguments ------------------------------------------
        DeclareLaunchArgument('group', description='Group name / number'),
        DeclareLaunchArgument('world', description='World name / number'),

        # ---------- marking node ---------------------------------------
        Node(
            package='challenge2ros2',
            executable='marking_node',
            name='marker',
            output='screen',
            parameters=[{
                'group': LaunchConfiguration('group'),
                'world': LaunchConfiguration('world'),
                'duration': 180,
            }],
            on_exit=Shutdown(),
        ),

        # ---------- explorer (external package) ------------------------
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([
                FindPackageShare('turtlebot3_bringup'),
                '/launch/robot.launch.py',
            ]),
        ),

        # ---------- explorer (external package) ------------------------
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([
                FindPackageShare('turtlebot_explorer'),
                '/launch/explorer.launch.py',
            ]),
        ),
    ])
