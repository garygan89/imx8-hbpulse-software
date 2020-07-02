#!/usr/bin/python
from eeg_lib_2 import ADS1299
from time import sleep


dev = ADS1299()
dev.reg_map()
