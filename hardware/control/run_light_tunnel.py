# MIT LICENSE

# Copyright 2023 Juan L. Gamella

# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# “Software”), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:

# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


import serial
import time
import argparse
import sys
import numpy as np
import control.protocol as prtcl
from control.board import Board
import control.camera as camera
from datetime import datetime
import os
from copy import deepcopy
import timeit

# Parse parameters
arguments = {
    "delay": {"default": 100, "type": int},
    "baud_rate": {"default": 500000, "type": int},
    "port": {"default": "/dev/ttyACM0", "type": str},
    "verbose": {"default": 1, "type": int},
    "protocol": {"type": str},
    "output_path": {"type": str, "default": "data_raw/"},
    "confirm": {"type": bool, "default": False},
}

parser = argparse.ArgumentParser(description="Run experiments")
for name, params in arguments.items():
    required = True
    if params["type"] == bool:
        options = {"action": "store_true"}
    else:
        options = {"action": "store", "type": params["type"]}
    if "default" in params:
        options["default"] = params["default"]
        required = False
    parser.add_argument("--" + name, dest=name, required=required, **options)

args = parser.parse_args()

# ----------------------------------------------------------------------
# Set-up camera


def print_csv(observations, file):
    observations = np.atleast_2d(observations)
    for obs in observations:
        string = ",".join(["%s" % v for v in obs])
        print(string, file=file)


camera_instructions = "Please set the following camera parameters by hand:\n"
camera_instructions += "  File Format -> JPEG\n"
camera_instructions += "  Silent Shooting -> On\n"
print(camera_instructions, file=sys.stderr)
if args.confirm:
    input("\nPress ENTER when ready")

print("Configuring camera...", file=sys.stderr, end="")
sys.stderr.flush()
cam = camera.Camera()
print(" done.", file=sys.stderr)
sys.stderr.flush()

camera_variables = ["aperture", "iso", "shutter_speed", "image_file"]

# ----------------------------------------------------------------------
# Main loop

protocol_name = args.protocol.split("/")[-1]
protocol_name = protocol_name.split(".txt")[0]
timestamp = datetime.now().strftime("%Y_%m_%d-%H_%M_%S")
log_filename = "logs/%s_%s.log" % (timestamp, protocol_name)
# Make directories
path = args.output_path + timestamp + "_" + protocol_name + "/"
os.mkdir(path)
images_directory = path + "images_full/"
os.mkdir(images_directory)
output_filename = path + timestamp + "_" + protocol_name + "_raw.csv"
print(f'\nSaving data to "{output_filename}"\n', file=sys.stderr)

IMG_COUNTER = 0

with open(output_filename, "w") as output_file:
    with open(log_filename, "w") as logfile:
        # Define the logging function: stderr + log file
        def log(msg, end="\n"):
            print(msg, end=end, file=sys.stderr)
            print(msg, end=end, file=logfile)
            sys.stderr.flush()
            sys.stdout.flush()

        log(args)

        # Open port and execute protocol
        log("Opening port %s at baud rate %d" % (args.port, args.baud_rate))
        with serial.Serial(args.port, args.baud_rate, timeout=None) as ser:
            board = Board(
                serial=ser, output_file=None, log_fun=log, verbose=args.verbose
            )

            # Write header with variable names
            header = ",".join(board.variables + camera_variables)
            print(header, file=output_file)
            output_file.flush()

            # Load and parse protocol
            log("Loading and parsing protocol")
            protocol = prtcl.load(args.protocol, board.variables + camera_variables)
            log("Protocol loaded")

            start_time = time.time()
            # Go through protocol, executing each instruction
            for i, instruction in enumerate(protocol):
                if instruction.kind == "SET" and instruction.target == "aperture":
                    log(f"Executing instruction {instruction}")
                    cam.set_aperture(instruction.value)
                elif instruction.kind == "SET" and instruction.target == "iso":
                    log(f"Executing instruction {instruction}")
                    cam.set_iso(instruction.value)
                elif (
                    instruction.kind == "SET" and instruction.target == "shutter_speed"
                ):
                    log(f"Executing instruction {instruction}")
                    cam.set_shutter_speed(instruction.value)
                elif instruction.kind == "MSR":
                    observations = []
                    # Take measurements together with images
                    sub_instruction = deepcopy(instruction)
                    sub_instruction.n = 1
                    for i in range(instruction.n):
                        observation = board.execute_instruction(sub_instruction)
                        timestamp = observation[0]
                        filename = str(IMG_COUNTER) + f"_{timestamp:d}" + ".jpg"
                        path = images_directory + filename
                        IMG_COUNTER += 1
                        cam.capture_and_store(path)
                        cam_parameters = [
                            cam.aperture,
                            cam.iso,
                            cam.shutter_speed,
                            filename,
                        ]
                        observation = np.hstack([observation[0], cam_parameters])
                        observations.append(observation)
                    # Print observations to the output file
                    print_csv(observations, file=output_file)
                    output_file.flush()
                else:
                    board.execute_instruction(instruction)

            # Tell board to reset and close serial connection
            board.reset()
            log(
                'Ran experiment for protocol "%s" in %0.2f seconds. Stored results in "%s"'
                % (args.protocol, time.time() - start_time, output_filename)
            )


# ----------------------------------------------------------------------
# Postprocess results
