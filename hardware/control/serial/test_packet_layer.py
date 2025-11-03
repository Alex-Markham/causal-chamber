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
from control.serial.packet import PacketLayer
import time
import base64

lines = [
    "I like to think (and",
    "the sooner the better!)",
    "of a cybernetic meadow",
    "where mammals and computers",
    "live together in mutually",
    "programming harmony",
    "like pure water",
    "touching clear sky.",
    "",
    "I like to think",
    "(right now, please!)",
    "of a cybernetic forest",
    "filled with pines and electronics",
    "where deer stroll peacefully",
    "past computers",
    "as if they were flowers",
    "with spinning blossoms.",
] * 100

with serial.Serial("/dev/ttyACM0", 500000, timeout=None) as ser:
    ser.reset_input_buffer()
    ser.reset_output_buffer()

    layer = PacketLayer(ser, verbose=3)
    print(ser.read(1))
    for line in lines:
        print()
        layer.send(line.encode())
        response = layer.receive()
        assert response == line.encode()
        # time.sleep(0.1)
