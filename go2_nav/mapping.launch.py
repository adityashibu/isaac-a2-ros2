"""Mapping bringup for the Go2 warehouse demo.

Runs:
  1. pointcloud_to_laserscan  (/unitree_go2/lidar/point_cloud -> /scan)
  2. slam_toolbox (async, mapping mode)
  3. RViz (nav2 default view)

The Isaac sim must already be running (it publishes /clock, /tf, and the
lidar point cloud). Save the map when done with:
  ros2 run nav2_map_server map_saver_cli -f ~/isaac-go2-ros2/go2_nav/maps/warehouse
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    this_dir = os.path.dirname(os.path.realpath(__file__))
    slam_params = os.path.join(this_dir, "slam_params.yaml")

    use_sim_time = LaunchConfiguration("use_sim_time")
    rviz_config = LaunchConfiguration("rviz_config")

    default_rviz = os.path.join(
        get_package_share_directory("nav2_bringup"), "rviz", "nav2_default_view.rviz"
    )

    pointcloud_to_laserscan = Node(
        package="pointcloud_to_laserscan",
        executable="pointcloud_to_laserscan_node",
        name="pointcloud_to_laserscan",
        remappings=[
            ("cloud_in", "/unitree_go2/lidar/point_cloud"),
            ("scan", "/scan"),
        ],
        parameters=[{
            "use_sim_time": use_sim_time,
            "target_frame": "unitree_go2/base_link",
            "transform_tolerance": 0.05,
            # Height slice relative to base_link (base sits ~0.42 m above floor):
            # -0.30 keeps the floor out, 1.0 catches low/high obstacles.
            "min_height": -0.30,
            "max_height": 1.0,
            "angle_min": -3.14159265,
            "angle_max": 3.14159265,
            "angle_increment": 0.0087,     # ~0.5 deg
            "scan_time": 0.025,            # sim runs at 40 Hz
            "range_min": 0.35,             # ignore self-returns
            "range_max": 20.0,
            "use_inf": True,
            "inf_epsilon": 1.0,
        }],
    )

    slam = Node(
        package="slam_toolbox",
        executable="async_slam_toolbox_node",
        name="slam_toolbox",
        output="screen",
        parameters=[slam_params, {"use_sim_time": use_sim_time}],
    )

    rviz = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        arguments=["-d", rviz_config],
        parameters=[{"use_sim_time": use_sim_time}],
        output="screen",
    )

    return LaunchDescription([
        DeclareLaunchArgument("use_sim_time", default_value="true"),
        DeclareLaunchArgument("rviz_config", default_value=default_rviz),
        pointcloud_to_laserscan,
        slam,
        rviz,
    ])
