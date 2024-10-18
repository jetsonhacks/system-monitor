# system-monitor
A web enabled system monitor for NVIDIA Jetson Development Kits

![Remote monitor of Jetson Nano](images/sys_mon_nano.gif)
## Work in progress

Building Documentation and Video, full article on JetsonHacks.com soon!

Requires Python 3.10+ - For Jetson Nano & Xaviers, consider using a virtual environment (e.g. Anaconda)

An example of creating a webserver to deliver a subset of system data such as CPU, GPU and memory usage.

Websockets allow refreshing the data easily.

You will need to install the requirements.txt
```
pip install -r requirements.txt
```

To enable WebSockets when connecting from another machine, you need to set the server address in the server_config.ini file. The IP address should be the IP address of the server (this) machine.

## Notes
* October, 2024
* Initial Release
* Tested on Jetson Nano, Jetson Xavier, and Jetson Orin
* Requires Python 3.10+
