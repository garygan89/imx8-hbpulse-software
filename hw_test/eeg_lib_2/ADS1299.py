from time import sleep, time
import mraa
from hardware import Hardware
from settings import Settings
from register import Register
#import paho.mqtt.publish as publish


class ADS1299(object):
    DEFAULT_SETTINGS = Settings()
    DEFAULT_SETTINGS.update({
        # === SPI Settings ===
        # 2.25MHz >= f(spi) >= 1.5MHz in spec.
        "SPI_FREQUENCY": int(2.25 * 10**6),
        "SPI_CHANNEL": 5,  # SPI channel in EEG block 1.2 is 5.
        "SPI_MODE": mraa.SPI_MODE1,  # SPI mode 1 in spec

        # === HARDWARE Settings ===
        "PIN_POWER": 46,
        "PIN_RESET": 32,
        "PIN_START": 45,
        "PIN_READY": 31,
        "PIN_CHIP_SELECT": 23,
        "PIN_CHIP_SELECT_2": 47,
    })

    @staticmethod
    def init_gpio(pin, dir, mode):
        # Set direction and pull-down/pull-up for an mraa gpio pin,
        # and return mraa.Gpio object.
        gpio = mraa.Gpio(pin)
        gpio.dir(dir)
        gpio.mode(mode)
        return gpio

    def __init__(self):
        # Initialize an ADS1299 object
        self.SETTINGS = Settings()
        self.SETTINGS.update(ADS1299.DEFAULT_SETTINGS)
        try:
            # Lazy import local settings when __init__ is called.
            # If local settings exist, overwrite this object settings.
            from .settings import LOCAL_SETTINGS
            self.SETTINGS.update(LOCAL_SETTINGS)
        except ImportError:
            pass
        
        # Initialize SPI for ADS1299
        self.spi = mraa.Spi(self.SETTINGS.SPI_CHANNEL)
        self.spi.frequency(self.SETTINGS.SPI_FREQUENCY)
        self.spi.mode(self.SETTINGS.SPI_MODE)
        
        # Initialize hardware control for ADS1299
        self.hardware = Hardware()
        self.hardware.power = self.init_gpio(
            self.SETTINGS.PIN_POWER, mraa.DIR_OUT_LOW, mraa.MODE_STRONG)
        self.hardware.reset = self.init_gpio(
            self.SETTINGS.PIN_RESET, mraa.DIR_OUT_HIGH, mraa.MODE_STRONG)
        self.hardware.start = self.init_gpio(
            self.SETTINGS.PIN_START, mraa.DIR_OUT_LOW, mraa.MODE_STRONG)
        self.hardware.ready = self.init_gpio(
            self.SETTINGS.PIN_READY, mraa.DIR_IN, mraa.MODE_HIZ)
        self.hardware.chip_select = self.init_gpio(
            self.SETTINGS.PIN_CHIP_SELECT, mraa.DIR_OUT_HIGH, mraa.MODE_STRONG
        )
        self.hardware.chip_select_2 = self.init_gpio(
            self.SETTINGS.PIN_CHIP_SELECT_2, mraa.DIR_OUT_HIGH, mraa.MODE_STRONG
        )
        self.hardware.power.write(1) # power up
        # wait for internal reference waking up (150ms)
        # wait for internal clock waking up (20us)
        # wait for external cloxk waking up (1.5ms)
        sleep(160 * 10**(-3))
        self.hardware.reset.write(0) # reset ADS1299
        sleep(1 * 10**(-3)) # wait for reset register (18 CLK)
        self.hardware.reset.write(1) # finish reseting ADS1299
        
        # Connect Register controller for ADS1299
        self.register = Register(self.spi, self.hardware.chip_select)

    @staticmethod
    def parse_data(data):
        # parse data
        message = "Good," if (data[0] & 0xC00000 == 0xC00000) else "Bad, "
        loffp = "".join(["T" if (data[0] & (1<<i)) else "F" for i in range(19, 11, -1)])
        loffn = "".join(["T" if (data[0] & (1<<i)) else "F" for i in range(11, 3, -1)])
        gpio = "".join(["I" if (data[0] & (1<<i)) else "O" for i in range(3, -1, -1)])
        channel = ",".join([str(data[_] - 2*(data[_]&0x800000)).rjust(10, ' ') for _ in range(1, 9)])
        message += "LOFF,(P):" + loffp + ",(N):" + loffn + ",GPIO:" + gpio + ",Data:" + channel
        return message
        
    def write_command(self, command):
        self.hardware.chip_select.write(0)
        self.spi.writeByte(command)
        self.hardware.chip_select.write(1)
        self.hardware.chip_select_2.write(0)
        self.spi.writeByte(command)
        self.hardware.chip_select_2.write(1)
    
    def wakeup(self):
        self.write_command(0x02)
    
    def standby(self):
        self.write_command(0x04)
    
    def reset(self):
        self.write_command(0x06)
    
    def start(self):
        self.write_command(0x08)
    
    def stop(self):
        self.write_command(0x0A)     

    def rdatac(self):
        self.write_command(0x10) 
    
    def sdatac(self):
        self.write_command(0x11)
    
    def rdata(self, init=False):
        # read data
        if init:
            self.start()
            self.sdatac()
        while self.hardware.ready.read() != 0:
            pass            
        # (RDATA + STATUS(3) + 8Channel*3Byte)
        command = bytearray(1 + 3 + 8*3)
        command[0] = 0x12  # RDATA
        self.hardware.chip_select.write(0)
        result = self.spi.write(command)[1:]
        self.hardware.chip_select.write(1)
        print ADS1299.parse_data([
            (result[_*3]<<16) + (result[_*3+1]<<8) + result[_*3+2] for _ in range(9)])

    def reg_map(self):
        self.sdatac()
        command = bytearray(2 + 0x18)
        command[0] = 0x20  # Read REG @ address 0x00
        command[1] = 0x17  # Read REG @ 0x18 registers
        self.hardware.chip_select.write(0)
        result = self.spi.write(command)[2:]
        self.hardware.chip_select.write(1)
        for _ in range(0x18):
            print ("0x" + hex(_)[2:].zfill(2)), ":", ("0x" + hex(result[_])[2:].zfill(2)), bin(result[_])[2:].zfill(8)
        
        command = bytearray(2 + 0x18)
        command[0] = 0x20  # Read REG @ address 0x00
        command[1] = 0x17  # Read REG @ 0x18 registers
        self.hardware.chip_select_2.write(0)
        result = self.spi.write(command)[2:]
        self.hardware.chip_select_2.write(1)
        for _ in range(0x18):
            print ("0x" + hex(_)[2:].zfill(2)), ":", ("0x" + hex(result[_])[2:].zfill(2)), bin(result[_])[2:].zfill(8)
    
    def overwirte_reg(self, value):
        command = bytearray(2) + value
        command[0] = 0x40  # Write REG @ address 0x00
        command[1] = 0x17  # Write REG @ 0x18 registers
        self.hardware.chip_select.write(0)
        self.spi.write(command)
        self.hardware.chip_select.write(1)
        
        command = bytearray(2) + value
        command[0] = 0x40  # Write REG @ address 0x00
        command[1] = 0x17  # Write REG @ 0x18 registers
        self.hardware.chip_select_2.write(0)
        self.spi.write(command)
        self.hardware.chip_select_2.write(1)
    
    def log(self, sample):
        file = open("EEG_log" + str(int(time())) + ".txt", 'w')
        file2 = open("EEG2_log" + str(int(time())) + ".txt", 'w')
        self.start()
        self.sdatac()
        command = bytearray(1 + 3 + 8*3)
        command[0] = 0x12  # RDATA
        while self.hardware.ready.read() != 0:
            pass    
        for _ in range(sample):
            while self.hardware.ready.read() != 0:
                pass
            #1
            self.hardware.chip_select.write(0)                
            result = self.spi.write(command)[4:]
            result = [(result[_*3]<<16) + (result[_*3+1]<<8) + result[_*3+2] for _ in range(8)]
            file.write(str(time()).ljust(15, ' ') + "".join([str(result[_] - 2*(result[_]&0x800000)).rjust(10, ' ') for _ in range(8)]) + "\n")
            self.hardware.chip_select.write(1)
            #2
            self.hardware.chip_select_2.write(0)
            result = self.spi.write(command)[4:]
            result = [(result[_*3]<<16) + (result[_*3+1]<<8) + result[_*3+2] for _ in range(8)]
            file2.write(str(time()).ljust(15, ' ') + "".join([str(result[_] - 2*(result[_]&0x800000)).rjust(10, ' ') for _ in range(8)]) + "\n")
            self.hardware.chip_select_2.write(1)

    def upload(self):
        broker_ip = '140.113.216.21'
        broker_port = '1883'
        topic = 'eeg/4/128'
        self.start()
        self.sdatac()
        self.hardware.chip_select.write(0)
        # (RDATA + STATUS(3) + 8Channel*3Byte)
        command = bytearray(1 + 3 + 8*3)

        command[0] = 0x12  # RDATA
        try:
            while True:
                msg = ""
                for i in range(32):
                    while self.hardware.ready.read() != 0:
                        pass            
                    result = self.spi.write(command)[1:]
                    result = [str((result[_*3]<<16) + (result[_*3+1]<<8) + result[_*3+2]) for _ in range(1,9)]
                    msg += str(time()) + "," + ",".join(result) + ";"
                #publish.single(topic, msg, hostname=broker_ip, port=broker_port)
        except KeyboardInterrupt:
           self.hardware.chip_select.write(1) 
