from glob import glob
import os

from setuptools import find_packages, setup

package_name = 'challenge2ros2'

setup(
    name=package_name,
    version='0.0.1',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'),
            glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'maps'),
            glob('maps/*')),
        (os.path.join('share', package_name, 'worlds'),
            glob('worlds/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='sh0041',
    maintainer_email='sh0041@surrey.ac.uk',
    description='TurtleBot explorer marking and evaluation for SLAM challenge',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'marking_node = challenge2ros2.marking_node:main',
        ],
    },
)
