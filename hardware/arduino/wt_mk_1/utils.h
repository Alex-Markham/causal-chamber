/* ; -*- mode: C++;-*- */

/*
   MIT License

   Copyright (c) 2023 Juan L. Gamella

   Permission is hereby granted, free of charge, to any person obtaining a copy
   of this software and associated documentation files (the "Software"), to deal
   in the Software without restriction, including without limitation the rights
   to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
   copies of the Software, and to permit persons to whom the Software is
   furnished to do so, subject to the following conditions:

   The above copyright notice and this permission notice shall be included in all
   copies or substantial portions of the Software.

   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
   IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
   FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
   AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
   LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
   OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
   SOFTWARE.
*/

#ifndef UTILS
#define UTILS

#include "rgb_lcd.h" // For RGB display

void fail( String msg);
void fail(String msg, String params);

/*-----------------------------------------------------------------------*/
/* Analog sensors: microphone, amplification signals, current */

void set_oversampling(unsigned int * setting, float value);
void set_reference_voltage(uint8_t * setting, float value);
float get_reference_voltage(uint8_t * setting); // Transform to float
float analog_avg(int pin, int samples, uint8_t reference);

/* ------------------------------------------------------------------- */
/* Instruction parser */

typedef enum instruction_type {
                               SET,
                               MSR,
                               RST,
                               UNK
};

struct Instruction {
  instruction_type type;
  String target;
  float p1;
  float p2;
};

Instruction decode_instruction(String instruction);

/* ------------------------------------------------------------------- */
/* LCD display */

extern rgb_lcd lcd;
void setup_display();
void set_display_color(byte red, byte green, byte blue);
void clear_top();
void clear_bottom();
void print_top(String msg);
void print_bottom(String msg);

#endif
