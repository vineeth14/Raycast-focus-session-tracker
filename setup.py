from setuptools import setup, find_packages

setup(
    name="raycast-focus-tracker",
    version="1.0.0",
    description="macOS menu bar app for tracking Raycast focus sessions",
    author="Vineeth Rajesh",
    packages=find_packages(),
    install_requires=[
        "rumps==0.4.0",
        "lesley==0.3.0", 
        "pandas==2.3.1"
    ],
    entry_points={
        'console_scripts': [
            'raycast-tracker=raycast_focus_tracker.daemon_launcher:main',
            'raycast-tracker-stop=raycast_focus_tracker.stop_tracker:main',
        ],
    },
    scripts=[
        'raycast_focus_tracker/focus-tracker.sh', 
        'raycast_focus_tracker/stop-tracker.sh',
        'raycast_focus_tracker/start-daemon.sh'
    ],
    include_package_data=True,
    package_data={
        'raycast_focus_tracker': ['*.sh'],
    },
    python_requires='>=3.8',
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: MacOS",
    ],
)