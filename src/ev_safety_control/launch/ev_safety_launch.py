from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        # 1. Safety Manager Logic (Backend)
        Node(
            package='ev_safety_control',
            executable='safety_manager',
            name='safety_manager',
            output='screen'
        ),
        
        # 2. Motor Controller (Hardware & Keyboard Input)
        # We use xterm so you have a dedicated window to type W/S/Space
        Node(
            package='ev_safety_control',
            executable='motor_controller',
            name='motor_controller',
            prefix=['xterm -hold -e'], 
            emulate_tty=True
        ),
        Node(
            package='ev_safety_control',
            executable='dashboard',
            name='ev_dashboard',
            output='screen'
        )
    ])