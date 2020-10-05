#!/bin/bash
MIN_BRIGHTNESS="00"
MAX_BRIGHTNESS="FF"
DIRECTION=$1
SLEEP_SEC=0.05

# Data format
# Command:         I2C/i2c           1/2         0/1        30/1F/58   reg_addr   size_of_bytes       reg_val            
# Description:     In capital/       I2C-        Read/      Slave         Register      1/2/4 Bytes of  Register
#                  Small             BUS       Write       address        address       register        Value

# Note: Use all the values (Slave address, Register address and Register value) in hexadecimal format.
# Slave address : 0x28 (LED driver)

# echo $DIRECTION

if [ $DIRECTION == 'left' ]; then # turn on left display
  echo "Enabling LEFT DISPLAY..."
  # left disp (channel 2)
  #echo "I2C 2 1 28 00 1 00" >> /dev/ttyACM0
  echo "I2C 2 1 28 01 1 $MAX_BRIGHTNESS" >> /dev/ttyACM0; sleep $SLEEP_SEC
  echo "I2C 2 1 28 02 1 $MAX_BRIGHTNESS" >> /dev/ttyACM0; sleep $SLEEP_SEC
  echo "I2C 2 1 28 03 1 $MAX_BRIGHTNESS" >> /dev/ttyACM0; sleep $SLEEP_SEC

# right disp (channel 1)
  #echo "I2C 1 1 28 00 1 00" >> /dev/ttyACM0
  echo "I2C 1 1 28 01 1 $MIN_BRIGHTNESS" >> /dev/ttyACM0; sleep $SLEEP_SEC
  echo "I2C 1 1 28 02 1 $MIN_BRIGHTNESS" >> /dev/ttyACM0; sleep $SLEEP_SEC
  echo "I2C 1 1 28 03 1 $MIN_BRIGHTNESS" >> /dev/ttyACM0; sleep $SLEEP_SEC

elif [ $DIRECTION == 'right' ]; then # turn on right display
  echo "Enabling RIGHT DISPLAY..."
# right disp (channel 1)
  # echo "I2C 1 1 28 00 1 00" >> /dev/ttyACM0
  echo "I2C 1 1 28 01 1 $MAX_BRIGHTNESS" >> /dev/ttyACM0; sleep $SLEEP_SEC
  echo "I2C 1 1 28 02 1 $MAX_BRIGHTNESS" >> /dev/ttyACM0; sleep $SLEEP_SEC
  echo "I2C 1 1 28 03 1 $MAX_BRIGHTNESS" >> /dev/ttyACM0; sleep $SLEEP_SEC  
  
  # left disp (channel 2)
  # echo "I2C 2 1 28 00 1 00" >> /dev/ttyACM0
  echo "I2C 2 1 28 01 1 $MIN_BRIGHTNESS" >> /dev/ttyACM0; sleep $SLEEP_SEC
  echo "I2C 2 1 28 02 1 $MIN_BRIGHTNESS" >> /dev/ttyACM0; sleep $SLEEP_SEC
  echo "I2C 2 1 28 03 1 $MIN_BRIGHTNESS" >> /dev/ttyACM0; sleep $SLEEP_SEC


fi



