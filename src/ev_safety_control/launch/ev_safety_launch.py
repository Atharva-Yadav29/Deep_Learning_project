from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='ev_safety_control',
            executable='vision_node',
            name='vision',
            output='screen'
        ),
        Node(
            package='ev_safety_control',
            executable='safety_manager',
            name='safety_manager',
            output='screen'
        ),
        Node(
            package='ev_safety_control',
            executable='websocket_node',
            name='websocket_dashboard',
            output='screen'
        ),
        Node(
            package='ev_safety_control',
            executable='motor_controller',
            name='motor_controller',
            output='screen',
            prefix='xterm -e' # Opens a separate terminal for W/S/Space keyboard driving
        )
    ])