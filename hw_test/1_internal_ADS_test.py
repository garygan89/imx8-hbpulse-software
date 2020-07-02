#!/usr/bin/python
from eeg_lib import ADS1299
from time import sleep


dev = ADS1299()
dev.register.reference_power = True
dev.register.BIAS_reference = True
dev.register.test_source = True
dev.register.BIAS_power = True
dev.register.CH1_power = False
dev.register.CH2_power = False
dev.register.CH3_power = False
dev.register.CH4_power = False
dev.register.CH5_power = False
dev.register.CH6_power = False
dev.register.CH7_power = False
dev.register.CH8_power = False
dev.register.CH1_MUX = 5
dev.register.CH2_MUX = 5
dev.register.CH3_MUX = 5
dev.register.CH4_MUX = 5
dev.register.CH5_MUX = 5
dev.register.CH6_MUX = 5
dev.register.CH7_MUX = 5
dev.register.CH8_MUX = 5
dev.register.sample_rate = 4
dev.sdatac()
dev.start()
dev.log(2000)
