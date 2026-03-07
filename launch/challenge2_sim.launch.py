"""Launch marking node with ground-truth map server and simulated explorer."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    pkg_share = FindPackageShare('challenge2ros2')

    return LaunchDescription([
        # ---------- arguments ------------------------------------------
        DeclareLaunchArgument('group', description='Group name / number'),
        DeclareLaunchArgument('world', description='World name / number'),
        DeclareLaunchArgument(
            'map_file',
            default_value=[
                pkg_share, '/maps/',
                LaunchConfiguration('world'), '.yaml',
            ],
            description='Path to ground-truth map YAML',
        ),

        # ---------- ground-truth map server (Nav2 lifecycle node) ------
        Node(
            package='nav2_map_server',
            executable='map_server',
            name='map_server',
            output='screen',
            parameters=[{
                'yaml_filename': LaunchConfiguration('map_file'),
            }],
            remappings=[('map', 'gt_map')],
        ),

        # Lifecycle manager – auto-activates the map_server node
        Node(
            package='nav2_lifecycle_manager',
            executable='lifecycle_manager',
            name='lifecycle_manager_map_server',
            output='screen',
            parameters=[{
                'autostart': True,
                'node_names': ['map_server'],
            }],
        ),

        # ---------- marking / scoring node -----------------------------
        Node(
            package='challenge2ros2',
            executable='marking_node',
            name='marker',
            output='screen',
            parameters=[{
                'group': LaunchConfiguration('group'),
                'world': LaunchConfiguration('world'),
                'duration': 60,
            }],
        ),

        # ---------- simulated explorer (external package) --------------
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([
                FindPackageShare('turtlebot_explorer'),
                '/launch/turtlebot_explorer_sim.launch.py',
            ]),
            launch_arguments={
                'world_file': [
                    pkg_share, '/worlds/',
                    LaunchConfiguration('world'), '.world',
                ],
            }.items(),
        ),
    ])
