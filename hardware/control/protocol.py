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


import re
import control.messages as messages


def load(filename, targets):
    # Load protocol into memory
    with open(filename, "r", encoding="UTF-8") as f:
        lines = [line.rstrip() for line in f]
        f.close()
    # Check all instructions have the correct syntax
    comment_regex = re.compile("^#.*$")
    parsed = []
    for i, line in enumerate(lines):
        if line == "":
            pass
        elif comment_regex.match(line) is not None:
            pass
        else:
            try:
                instruction = messages.parse(line)
                if instruction.kind == "SET" and instruction.target not in targets:
                    raise SyntaxError(
                        f'Line {i}: target "{instruction.target}" does not match any variables on board'
                    )
                parsed.append(instruction)
            except ValueError as e:
                raise ValueError(
                    f'Line {i}: "{line}" does not match any valid instructions.'
                ) from e
    return parsed
