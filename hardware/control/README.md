# control/

This directory contains the Python code to connect and communicate with the chambers, and run experiments.

- [`serial`](serial/) contains an implementation of error-less serial communication, inspired by the [TCP](https://en.wikipedia.org/wiki/Transmission_Control_Protocol) protocol
- [`board.py`](board.py) contains the high-level code to initiate a connection with a chamber and send instructions / receive data
- [`protocol.py`](protocol.py) contains the definitions of the experiment protocol language and the code to parse and load experiment protocols
- [`interpreter.py`](interpreter.py) can be run as a script to initiate a connection to a chamber (provided parameters `--port` and `--baud_rate`) and send instructions to it in a shell-like manner.
- [`run_experiment.py`](run_experiment.py) can be run as a script to run an experiment protocol and store the resulting data; [`run_light_tunnel.py`](run_light_tunnel.py) must be used instead if running the light tunnel in its _camera_ configuration

To run this code, you must

- Install python dependencies in requirements.txt
- For linux, add user to the serialout group and restart the computer
```
sudo usermod -a -G dialout <username>
```

