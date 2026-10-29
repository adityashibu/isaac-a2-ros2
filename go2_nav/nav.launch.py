"""Navigation bringup for the Go2 warehouse demo.

Runs on top of the already-running Isaac sim (which provides /clock, /tf
odom->base_link, and the lidar point cloud):

  1. pointcloud_to_laserscan  (/unitree_go2/lidar/point_cloud -> /scan)
  2. localization  (map_server with the saved map + AMCL)   [nav2_bringup]
  3. navigation   (planner, MPPI controller, BT navigator, ...) [nav2_bringup]
     with /cmd_vel remapped to /unitree_go2/cmd_vel so Nav2 drives the dog.
  4. RViz (nav2 default view) for clicking Nav2 goals.

AMCL's initial pose is preset in nav2_params.yaml, so no manual 2D Pose
Estimate is needed. Launch the Isaac sim first, then:
  ros2 launch ~/isaac-go2-ros2/go2_nav/nav.launch.py
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node, SetRemap


def generate_launch_description():
    this_dir = os.path.dirname(os.path.realpath(__file__))
    nav2_bringup = get_package_share_directory("nav2_bringup")

    use_sim_time = LaunchConfiguration("use_sim_time")
    map_yaml = LaunchConfiguration("map")
    params_file = LaunchConfiguration("params_file")
    rviz_config = LaunchConfiguration("rviz_config")
    autostart = LaunchConfiguration("autostart")

    default_map = os.path.join(this_dir, "maps", "warehouse.yaml")
    default_params = os.path.join(this_dir, "nav2_params.yaml")
    default_rviz = os.path.join(nav2_bringup, "rviz", "nav2_default_view.rviz")

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
            # Raised from -0.30: base_link sits ~0.42 m above the floor, and the
            # gait bob tilts the lidar so floor returns would sweep into a low
            # slice and look like obstacles ahead. -0.10 keeps the floor out
            # while still catching obstacles taller than ~0.32 m. Lower it if
            # short obstacles are missed; raise it if phantom hits return.
            "min_height": -0.10,
            "max_height": 1.0,
            "angle_min": -3.14159265,
            "angle_max": 3.14159265,
            "angle_increment": 0.0087,
            "scan_time": 0.025,
            "range_min": 0.35,
            "range_max": 20.0,
            "use_inf": True,
            "inf_epsilon": 1.0,
        }],
    )

    # Localization. The sim's odom is ground truth and the saved map was built
    # from it at the fixed spawn pose, so map == odom (identity). A static
    # map->odom gives exact localization and avoids AMCL scan-match jitter,
    # which made the believed pose drift and the dog clip mapped racks. Only
    # map_server is run from nav2 (to publish the map); no AMCL.
    map_server = Node(
        package="nav2_map_server",
        executable="map_server",
        name="map_server",
        output="screen",
        parameters=[{"use_sim_time": use_sim_time, "yaml_filename": map_yaml}],
    )
    localization_mgr = Node(
        package="nav2_lifecycle_manager",
        executable="lifecycle_manager",
        name="lifecycle_manager_localization",
        output="screen",
        parameters=[{"use_sim_time": use_sim_time, "autostart": autostart,
                     "node_names": ["map_server"]}],
    )
    map_to_odom = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        name="static_map_to_odom",
        arguments=["--frame-id", "map", "--child-frame-id", "odom"],
        parameters=[{"use_sim_time": use_sim_time}],
    )

    # Nav2 controller publishes "cmd_vel"; remap it to the sim's drive topic so
    # the whole navigation stack commands the Go2.
    navigation = GroupAction([
        SetRemap(src="/cmd_vel", dst="/unitree_go2/cmd_vel"),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(nav2_bringup, "launch", "navigation_launch.py")
            ),
            launch_arguments={
                "use_sim_time": use_sim_time,
                "params_file": params_file,
                "autostart": autostart,
            }.items(),
        ),
    ])

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
        DeclareLaunchArgument("map", default_value=default_map),
        DeclareLaunchArgument("params_file", default_value=default_params),
        DeclareLaunchArgument("rviz_config", default_value=default_rviz),
        DeclareLaunchArgument("autostart", default_value="true"),
        pointcloud_to_laserscan,
        map_server,
        localization_mgr,
        map_to_odom,
        navigation,
        rviz,
    ])
