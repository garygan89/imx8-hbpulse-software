#!/usr/bin/python
from eeg_lib_2 import ADS1299
from time import sleep


dev = ADS1299()
while True:
	sleep(1)
	print(1)
	a = bytearray([0x3e,0xd5,0xd0,0xfc,0xe0,0x20,0x20,0x20,0x20,0x20,0x20,0x20,0x20,0xff,0xff,0xff,0x00,0x00,0x00,0x00,0xf0,0x20,0x00,0x02])
	dev.overwirte_reg(a)
	sleep(1)
	print(0)
	a = bytearray([0x3e,0xd5,0xd0,0xfc,0xe0,0x20,0x20,0x20,0x20,0x20,0x20,0x20,0x20,0xff,0xff,0xff,0x00,0x00,0x00,0x00,0x00,0x20,0x00,0x02])
        dev.overwirte_reg(a)