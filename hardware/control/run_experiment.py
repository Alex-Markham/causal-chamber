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
from datetime import datetime


# Parse parameters
arguments = {
    "delay": {"default": 4000, "type": int},  # Milliseconds to wait for board to reset
    "baud_rate": {"default": 500000, "type": int},
    "port": {"default": "/dev/ttyACM0", "type": str},
    "verbose": {"default": 1, "type": int},
    "protocol": {"type": str},
    "output_path": {"type": str, "default": "data_raw/"},
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
# Main loop

protocol_name = args.protocol.split("/")[-1]
protocol_name = protocol_name.split(".txt")[0]
timestamp = datetime.now().strftime("%Y_%m_%d-%H_%M_%S")
log_filename = "logs/%s_%s.log" % (timestamp, protocol_name)
output_filename = args.output_path + timestamp + "_" + protocol_name + ".csv"
print(f'\nSaving data to "{output_filename}"\n', file=sys.stderr)

with open(output_filename, "w") as output_file:
    with open(log_filename, "w") as logfile:

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
                serial=ser,
                output_file=output_file,
                log_fun=log,
                verbose=args.verbose,
            )

            # Write header with variable names
            header = ",".join(board.variables)
            print(header, file=output_file)

            # Load and parse protocol
            log("Loading and parsing protocol")
            protocol = prtcl.load(args.protocol, board.variables)
            log("Protocol loaded")

            start_time = time.time()
            # Go through protocol, executing each instruction
            for i, instruction in enumerate(protocol):
                board.execute_instruction(instruction)

            # Tell board to reset and close serial connection
            board.reset()
            time.sleep(args.delay / 1000)
            log(
                'Ran experiment for protocol "%s" in %0.2f seconds. Stored results in "%s"'
                % (args.protocol, time.time() - start_time, output_filename)
            )
            print(board.comms)
