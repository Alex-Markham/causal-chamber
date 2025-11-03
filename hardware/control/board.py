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

import timeit
import time
import numpy as np
import sys
import control.messages as messages
from control.serial.packet import PacketLayer
from control.serial.segment import TransportLayer

"""Module defining the Board class used to
communicate with the control board of each chamber.

"""

OBSERVATION_READ_TIMEOUT = 1  # timeout between bytes from observations
WAITING_FOR_START = "waiting_for_start"
READING = "reading"
DATA_PARSED = "data_parsed"
START_SYMBOL = b"<"
END_SYMBOL = b">"
MAX_COUNTER = np.single(100000.0)


class Board:
    def __init__(self, serial, output_file=sys.stdout, log_fun=None, verbose=0):
        """Given a serial connection to the board, reset the board and store
        the board's variable names.

        Parameters
        ----------
        serial : serial.TransportLayer
            The serial connection object, obtained from calling
            serial.Serial (see pySerial library).
        output_file : file object or NoneType
            Where to output the observations received from the board
            in CSV format. If None, there is no output (see
            Board.take_measurements)
        log_fun : function or NoneType, default=None
            The function used to log any debug messages, must take a
            string as first argument.
        verbose : int
            Whether to print messages sent/received from board and
            debug traces. Higher values correspond to increased
            verbosity: 0 - no output, 1 - High-level traces, 2 -
            Messages sent/received from board, 3 - raw messages
            received from board and timeout changes.

        Returns
        -------
        variables : list of string
            The list of variables returned by

        """
        self.serial = serial
        self.output_file = output_file
        self.last_observation = np.single(
            -1
        )  # To keep track of observations send by the board

        # Wrap log function to filter by verbosity
        def log(string, verbosity_level=1, **kwargs):
            if verbosity_level <= self.verbose:
                log_fun(string, **kwargs)

        self.log = log

        self.verbose = verbose

        # Clear the input and output buffers
        self.log("Clearing buffers")
        self.serial.reset_input_buffer()
        self.serial.reset_output_buffer()

        # Initializing protocol
        self.log("Initializing communication layers")
        self.comms = TransportLayer(
            PacketLayer(self.serial, log_fun, verbose=3 if verbose > 3 else 0),
            log_fun,
            verbose=verbose,
        )

        self.log("Resetting board")
        # Send reset signal to arduino
        self.serial.setDTR(False)
        self.serial.setDTR(True)
        self.log("Waiting for chamber to come online")

        # Receive chamber configuration identifier
        while True:
            try:
                response = messages.parse(self.comms.receive())
                if response.kind == "CHAMBER_CONFIG":
                    break
            except Exception as e:
                print(e)
        # Store chamber configuration
        self.log(f"Received chamber config: {response.config}")
        self.chamber_config = response.config

        # Receive chamber variables
        while True:
            try:
                response = messages.parse(self.comms.receive())
                if response.kind == "VARIABLES_LIST":
                    break
            except Exception as e:
                print(e)
        # Parse and store variable names
        self.log("Received variable names")
        # Compute length of a single observation block sent by the
        # board (note: arduino floats are 4 bytes = np.single)
        self.n_bytes = len(response.variables) * 4
        # Add variables computed in this machine, i.e. the timestamp and config
        self.variables = ["timestamp", "config"] + response.variables
        for i, var in enumerate(self.variables):
            log(f"  {i-2} : {var}")

    def execute_instruction(self, instruction):
        """Execute an instruction, i.e. wait, set a variable, take
        measurements or reset the board.

        """
        self.log(f"\nExecuting instruction {instruction}")
        if instruction.kind == "WAIT_INPUT":
            input(instruction.prompt)
        elif instruction.kind == "WAIT":
            seconds = instruction.wait / 1000
            self.log("  waiting for %0.4f seconds" % seconds)
            time.sleep(seconds)
        elif instruction.kind == "SET":
            self.set_variable(instruction)
        elif instruction.kind == "MSR":
            return self.take_measurements(instruction)
        elif instruction.kind == "RST":
            self.reset()  # TODO: maybe this resets the current object?

    def set_variable(self, instruction):
        if instruction.kind != "SET":
            raise ValueError(f'Wrong instruction type "{instruction}".')
        self.comms.send(f"SET,{instruction.target},{instruction.value}")
        response = messages.parse(self.comms.receive())
        if response.kind != "OK":
            raise Exception(f"Unexpected response from board: {response}")

    def reset(self):
        self.comms.send("RST")
        response = messages.parse(self.comms.receive())
        if response.kind != "OK":
            raise Exception(f"Unexpected response from board: {response}")

    def take_measurements(self, instruction):
        if instruction.kind != "MSR":
            raise ValueError(f'Wrong instruction type "{instruction}".')

        # Send MSR instruction
        self.comms.send(f"MSR,{instruction.n},{instruction.wait}")
        # Receive and check confirmation
        response = messages.parse(self.comms.receive())
        if response.kind != "OK" or response.args[0] != "MSR":
            raise Exception(f"Unexpected response from board: {response}")

        # Initialize buffer
        observations = np.zeros((instruction.n, len(self.variables)), dtype=object)

        # Reception loop
        count = 0
        while count < instruction.n:
            # Await response
            data_bytes = self.comms.receive()
            if len(data_bytes) != self.n_bytes:
                raise Exception(
                    f"Expected {self.n_bytes} bytes ({len(self.variables) - 1} variables), got {len(data_bytes)}."
                )
            observation = np.frombuffer(data_bytes, dtype=np.single)
            # Check that counter matches
            next_counter = (
                self.last_observation + 1
                if self.last_observation < MAX_COUNTER
                else 0.0
            )
            if observation[0] == next_counter:
                self.last_observation = observation[0]
            else:
                raise Exception(
                    f"Expected observation counter {self.last_observation+1}, got {observation[0]}."
                )
            observations[count, 0] = timeit.default_timer()
            observations[count, 1] = self.chamber_config
            observations[count, 2:] = observation

            # If required, directly print observation to output file (in CSV format)
            if self.output_file is not None:
                string = ",".join(["%s" % v for v in observations[count]])
                print(string, file=self.output_file)
                self.output_file.flush()
            count += 1
            self.log(f"  received observation {count}/{instruction.n}       ", end="\r")
        # Await for board to confirm that all observations were sent with <OK,DONE>
        response = messages.parse(self.comms.receive())
        if response.kind == "OK" and response.args[0] == "DONE":
            return observations
        else:
            raise Exception(f"Unexpected response from board: {response}")


# TODO: Instruction class -> str method just prints it raw
# Define a board error?
