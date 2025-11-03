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

/* See the Si115X datasheet https://www.silabs.com/documents/public/data-sheets/si115x-datasheet.pdf */

#include <Arduino.h>
#include "Si115X.h"


/**
 * Writes data over i2c
 */
void Si115X::write_data(uint8_t addr, uint8_t *data, size_t len){
  Wire.beginTransmission(addr);
  Wire.write(data, len);
  Wire.endTransmission();
}

/**
 * Reads data from a register over i2c
 */
int Si115X::read_register(uint8_t addr, uint8_t reg, int bytesOfData){
  int val = -1;
  
  Si115X::write_data(addr, &reg, sizeof(reg));
  Wire.requestFrom(addr, bytesOfData);
  
  if(Wire.available())
    val = Wire.read();
	
  return val;
}

/**
 * param set as shown in the datasheet
 */
void Si115X::param_set(uint8_t loc, uint8_t val){
  uint8_t packet[2];
  int r;
  int cmmnd_ctr;

  do {
    cmmnd_ctr = Si115X::read_register(Si115X::DEVICE_ADDRESS, Si115X::RESPONSE_0, 1);
      
    packet[0] = Si115X::HOSTIN_0;
    packet[1] = val;
    Si115X::write_data(Si115X::DEVICE_ADDRESS, packet, sizeof(packet));
      
    packet[0] = Si115X::COMMAND;
    packet[1] = loc | (0B10 << 6);
    Si115X::write_data(Si115X::DEVICE_ADDRESS, packet, sizeof(packet));
      
    r = Si115X::read_register(Si115X::DEVICE_ADDRESS, Si115X::RESPONSE_0, 1);	    
  } while(r > cmmnd_ctr); 
}

/**
 * param query as shown in the datasheet
 */
int Si115X::param_query(uint8_t loc){
  int result = -1;
  uint8_t packet[2];
  int r;
  int cmmnd_ctr;

  do {
    cmmnd_ctr = Si115X::read_register(Si115X::DEVICE_ADDRESS, Si115X::RESPONSE_0, 1);
	    
    packet[0] = Si115X::COMMAND;
    packet[1] = loc | (0B01 << 6);
	    
    Si115X::write_data(Si115X::DEVICE_ADDRESS, packet, sizeof(packet));
	    
    r = Si115X::read_register(Si115X::DEVICE_ADDRESS, Si115X::RESPONSE_0, 1);
  } while(r > cmmnd_ctr);
	
  result = Si115X::read_register(Si115X::DEVICE_ADDRESS, Si115X::RESPONSE_1, 1);
	
  return result;
}

/**
 * Send a command to the Si115X board.
 *
 * @param code The command code to be sent to the sensor (see datasheet)
 * @return 0 if succesful. If RESPONSE0 contained an error on initial read, a negative integer mapping to the error codes:
 *   - (-1) to 0x0 (Invalid command)
 *   - (-2) to 0x1 (Parameter access to an invalid location)
 *   - (-3) to 0x2 (Saturation of the ADC or overflow of accumulation)
 *   - (-4) to 0x3 (Output buffer overflow—this can happen when Burst mode is enabled and configured for greater than 26 bytes of output)
 * If RESPONSE0 contained an error after executing the command, a positive integer mapping to the error codes:
 *   - (1) to 0x0
 *   - (2) to 0x1
 *   - (3) to 0x2
 *   - (4) to 0x3
 * And 17 after reading RESPONSE0 more than MAX_RETRIES without seeing a counter increment.
 */

#define MAX_RETRIES 10000

int Si115X::send_command(uint8_t code, bool force){
  // Read state of RESPONSE0 before executing the command
  uint8_t initial_read = Si115X::read_register(Si115X::DEVICE_ADDRESS, Si115X::RESPONSE_0, 1);
  int initial_cmd_ctr = initial_read & Si115X::CMD_CTR;
  // If RESPONSE0 contained an error, return it
  if ((initial_read & Si115X::CMD_ERR) && !force)
    return (initial_cmd_ctr + 1) * -1;
  // Otherwise, assemble and send command
  uint8_t packet[2];
  packet[0] = Si115X::COMMAND;
  packet[1] = code;    
  Si115X::write_data(Si115X::DEVICE_ADDRESS, packet, sizeof(packet));
  // Read RESPONSE0 until counter increments or an error is communicated, or maximum number of retries is reached
  uint8_t response;
  int cmd_ctr;
  for(int i=0; i < MAX_RETRIES; i++) {
    response = Si115X::read_register(Si115X::DEVICE_ADDRESS, Si115X::RESPONSE_0, 1);
    cmd_ctr = response & Si115X::CMD_CTR;
    // RESPONSE0 contains an error
    if (response & Si115X::CMD_ERR)
      return cmd_ctr + 1;
    // Counter increased (or went back to 0)
    else if (cmd_ctr > initial_cmd_ctr || (initial_cmd_ctr == 15 & cmd_ctr == 0))
      return 0;
  }
  // Maximum number of retries reached
  return 17;
}


// bool Si115X::Begin(void){
//   Wire.begin();
//   // Wire.setClock(400000);
//   if (ReadByte(0x00) != 0x51) { // TODO: This should be read register
//     return false;
//   }
//   Si115X::send_command(Si115X::START, );

//   Si115X::param_set(Si115X::CHAN_LIST, 0B000010);

//   Si115X::param_set(Si115X::MEASRATE_H, 0);
//   Si115X::param_set(Si115X::MEASRATE_L, 1);  // 1 for a base period of 800 us
//   Si115X::param_set(Si115X::MEASCOUNT_0, 5); 
//   Si115X::param_set(Si115X::MEASCOUNT_1, 10);
//   Si115X::param_set(Si115X::MEASCOUNT_2, 10);
//   Si115X::param_set(Si115X::THRESHOLD0_L, 200);
//   Si115X::param_set(Si115X::THRESHOLD0_H, 0);
    

//   Wire.beginTransmission(Si115X::DEVICE_ADDRESS);
//   Wire.write(Si115X::IRQ_ENABLE);
//   Wire.write(0B000010);
//   Wire.endTransmission();
//   uint8_t conf[4];
// }

/**
 * Read the 16 bit output of the sensor on registers HOSTOUT_0 and HOSTOUT_1
 *
 * @return a positive integer with the sensor output, -1 if the reading was not succesful.
 */
LightReading Si115X::read_output() {
  LightReading result;
  int data[4];
  data[0] = Si115X::read_register(Si115X::DEVICE_ADDRESS, Si115X::HOSTOUT_0, 1);
  data[1] = Si115X::read_register(Si115X::DEVICE_ADDRESS, Si115X::HOSTOUT_1, 1);
  data[2] = Si115X::read_register(Si115X::DEVICE_ADDRESS, Si115X::HOSTOUT_2, 1);
  data[3] = Si115X::read_register(Si115X::DEVICE_ADDRESS, Si115X::HOSTOUT_3, 1);
  if (data[0] < 0 || data[1] < 0 || data[2] < 0 || data[3] < 0)
    result.ok = -1;
  else {
    result.ok = 0;
    // Process infrared reading (verbosity for proper casting into floats)
    result.ir = data[0];
    result.ir = result.ir * 256;
    result.ir = result.ir + data[1];
    // Process visible reading
    result.vis = data[2];
    result.vis = result.vis * 256;
    result.vis = result.vis + data[3];
  }
  return result;
}

uint8_t Si115X::ReadByte(uint8_t Reg) {
  Wire.beginTransmission(Si115X::DEVICE_ADDRESS);
  Wire.write(Reg);
  Wire.endTransmission();
  Wire.requestFrom(Si115X::DEVICE_ADDRESS, 1);
  return Wire.read();
}
