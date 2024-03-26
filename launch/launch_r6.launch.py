import os

from ament_index_python.packages import get_package_share_directory


from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, FindExecutable, LaunchConfiguration, PathJoinSubstitution
from launch.actions import RegisterEventHandler
from launch.event_handlers import OnProcessStart
from launch.actions import DeclareLaunchArgument
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch.conditions import IfCondition

def generate_launch_description():

    package_name='r6' 

    declared_arguments = []

    declared_arguments.append(
        DeclareLaunchArgument(
            "enable_joint0",
            default_value="true",
        )
    )

    declared_arguments.append(
        DeclareLaunchArgument(
            "enable_joint1",
            default_value="true",
        )
    )

    declared_arguments.append(
        DeclareLaunchArgument(
            "joint0_controller",
            default_value="joint0_velocity_controller",
        )
    )

    declared_arguments.append(
        DeclareLaunchArgument(
            "joint1_controller",
            default_value="joint1_velocity_controller",
        )
    )

    enable_joint0 = LaunchConfiguration("enable_joint0")
    enable_joint1 = LaunchConfiguration("enable_joint1")
    joint0_controller = LaunchConfiguration("joint0_controller")
    joint1_controller = LaunchConfiguration("joint1_controller")

    robot_description_content = Command(
        [
            PathJoinSubstitution([FindExecutable(name="xacro")]),
            " ",
            PathJoinSubstitution(
                [
                    FindPackageShare("r6"),
                    "urdf",
                    "odrive.urdf.xacro",
                ]
            ),
            " ",
            "enable_joint0:=",
            enable_joint0,
            " ",
            "enable_joint1:=",
            enable_joint1,
        ]
    )
    robot_description = {"robot_description": robot_description_content}

    robot_controllers = PathJoinSubstitution(
        [
            FindPackageShare("r6"),
            "config",
            "diffbot_controllers.yaml",
        ]
    )


    rsp = IncludeLaunchDescription(
                PythonLaunchDescriptionSource([os.path.join(
                    get_package_share_directory(package_name),'launch','rsp.launch.py'
                )]), launch_arguments={'use_sim_time': 'false', 'use_ros2_control': 'true'}.items()
    )

    robot_description = {"robot_description": robot_description_content}

    robot_controllers = PathJoinSubstitution(
        [
            FindPackageShare("r6"),
            "config",
            "diffbot_controllers.yaml",
        ]
    )

    control_node = Node(
        package="controller_manager",
        executable="ros2_control_node",
        output="both",
        parameters=[robot_description, robot_controllers],
    )
    
    delayed_controller_manager = TimerAction(period=3.0, actions=[control_node])

    diff_drive_spawner = Node(
        package="controller_manager",
        executable="spawner.py",
        arguments=["diff_cont"],
    )

    delayed_diff_drive_spawner = RegisterEventHandler(
        event_handler=OnProcessStart(
            target_action=controller_manager,
            on_start=[diff_drive_spawner],
        )
    )

    joint_broad_spawner = Node(
        package="controller_manager",
        executable="spawner.py",
        arguments=["joint_state_broadcaster", "-c", "/controller_manager"],
    )

    delayed_joint_broad_spawner = RegisterEventHandler(
        event_handler=OnProcessStart(
            target_action=controller_manager,
            on_start=[joint_broad_spawner],
        )
    )

    joint0_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[joint0_controller, "-c", "/controller_manager"],
        condition=IfCondition(enable_joint0),
    )

    joint1_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[joint1_controller, "-c", "/controller_manager"],
        condition=IfCondition(enable_joint1),
    )

    # Launch them all!
    nodes = [
        rsp,
        delayed_controller_manager,
        delayed_diff_drive_spawner,
        delayed_joint_broad_spawner,
        joint0_controller_spawner,
        joint1_controller_spawner,
    ]
    
    return LaunchDescription(declared_arguments + nodes)