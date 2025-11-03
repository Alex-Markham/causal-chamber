// MIT License

// Copyright (c) 2017 Infineon Technologies AG

// Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

// The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

#ifndef DPS310_H_INCLUDED
#define DPS310_H_INCLUDED

#include "DpsClass.h"
#include "dps310_config.h"

class Dps310 : public DpsClass
{
public:
  int16_t getContResults(float *tempBuffer, uint8_t &tempCount, float *prsBuffer, uint8_t &prsCount);

  /**
   * @brief Set the source of interrupt (FIFO full, measurement values ready)
   * 
   * @param intr_source Interrupt source as defined by Interrupt_source_310_e
   * @param polarity 
   * @return status code 
   */
  int16_t setInterruptSources(uint8_t intr_source, uint8_t polarity = 1);

protected:
  uint8_t m_tempSensor;

  //compensation coefficients
  int32_t m_c0Half;
  int32_t m_c1;

  /////// implement pure virtual functions ///////

  void init(void);
  int16_t configTemp(uint8_t temp_mr, uint8_t temp_osr);
  int16_t configPressure(uint8_t prs_mr, uint8_t prs_osr);
  int16_t readcoeffs(void);
  int16_t flushFIFO();
  float calcTemp(int32_t raw);
  float calcPressure(int32_t raw);
};

#endif
