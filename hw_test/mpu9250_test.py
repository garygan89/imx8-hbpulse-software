#!/usr/bin/python
import mraa
from time import sleep
import struct


dev = mraa.I2c(6)
dev.frequency(mraa.I2C_STD)
dev.address(0x68)
def readData(reg):
    value = (dev.readReg(reg)<<8) + dev.readReg(reg+1)
    return struct.unpack(">h", struct.pack(">H", value))[0]

while True:
    print (
        readData(59),
        readData(61),
        readData(63),
        readData(67),
        readData(69),
        readData(71),
    )
    sleep(0.1)
