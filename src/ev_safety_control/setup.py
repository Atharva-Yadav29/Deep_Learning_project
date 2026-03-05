import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'ev_safety_control'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # This line tells ROS to install all files from your launch/ folder
        (os.path.join('share', package_name, 'launch'), glob(os.path.join('launch', '*launch.[pxy][yma]*'))),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='atharva',
    maintainer_email='atharva@todo.todo',
    description='Intelligent EV Safety Assistant with ROS2 and YOLOv8',
    license='TODO: License declaration',
    extras_require={
        'test': ['pytest'],
    },
    entry_points={
    'console_scripts': [
        'safety_manager = ev_safety_control.safety_manager:main',
        'motor_controller = ev_safety_control.motor_controller_node:main', # Corrected
        'dashboard = ev_safety_control.dashboard:main',
    ],
},
)