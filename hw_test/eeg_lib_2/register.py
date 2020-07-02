class Register(object):
    class RegistNotExist(Exception):
        pass
    
    def lookup_generator(table):
        # table lookup fucntion generator
        def table_lookuper(value, table=table):
            try:
                return table[value]
            except KeyError:
                return "Error"
        table_lookuper.table = table
        return table_lookuper
    
    def boolean_generator(t_value, f_value):
        # boolean value lookup fucntion generator
        def boolean_lookuper(value, t_value=t_value, f_value=f_value):
            return t_value if value else f_value
        boolean_lookuper.table = {True: t_value, False: f_value}
        return boolean_lookuper
        
    REGISTER_MAP = {
        "sample_rate": {
            "address": 0x01,
            "mask": 0b00000111,
            "format": lookup_generator({
                0: "16kSPS", 1: "8kSPS", 2: "4kSPS", 3: "2kSPS",
                4: "1kSPS", 5: "500SPS", 6: "250SPS", 7: "N/A",
            })
        },
        "test_source": {
            "address": 0x02,
            "mask": 0b00010000,
            "format": boolean_generator("internal", "external")
        },
        "test_amplitude": {
            "address": 0x02,
            "mask": 0b00000100,
            "format": boolean_generator("2*(VREFP-VREFN)/2.4mV",
                                        "1*(VREFP-VREFN)/2.4mV")
        },
        "test_frequency": {
            "address": 0x02,
            "mask": 0b00000011,
            "format": lookup_generator({
                0: "1Hz", 1: "2Hz", 2: "Not used", 3: "DC",
            })
        },
        "reference_power": {
            "address": 0x03,
            "mask": 0b10000000,
            "format": boolean_generator("ON", "OFF")
        },
        "BIAS_measurement": {
            "address": 0x03,
            "mask": 0b00010000,
            "format": boolean_generator("Connect", "Disconnect")
        },
        "BIAS_reference": {
            "address": 0x03,
            "mask": 0b00001000,
            "format": boolean_generator("internal", "external")
        },
        "BIAS_power": {
            "address": 0x03,
            "mask": 0b00000100,
            "format": boolean_generator("ON", "OFF")
        },
        "SRB1": {
            "address": 0x15,
            "mask": 0b00100000,
            "format": boolean_generator("ON", "OFF")
        },
    }
    
    for i in range(0,4):
        REGISTER_MAP["GPIO" + str(i+1) + "_dir"] = {
            "address": 0x014,
            "mask": 1 << i,
            "format": boolean_generator("Input", "Output")
        }
        REGISTER_MAP["GPIO" + str(i+1) + "_data"] = {
            "address": 0x014,
            "mask": 0x10 << i,
            "format": boolean_generator("1", "0")
        }
    
    for i in range(0,8):
        REGISTER_MAP["CH" + str(i+1) + "_power"] = {
            "address": 0x05 + i,
            "mask": 0b10000000,
            "format": boolean_generator("OFF", "ON")
        }
        REGISTER_MAP["CH" + str(i+1) + "_gain"] = {
            "address": 0x05 + i,
            "mask": 0b01110000,
            "format": lookup_generator({
                0: "1", 16: "2", 32: "4", 48: "6",
                64: "8", 80: "12", 96: "24", 112: "N/A",
            })
        }
        REGISTER_MAP["CH" + str(i+1) + "_SRB2"] = {
            "address": 0x05 + i,
            "mask": 0b00001000,
            "format": boolean_generator("ON", "OFF")
        }
        REGISTER_MAP["CH" + str(i+1) + "_MUX"] = {
            "address": 0x05 + i,
            "mask": 0b00000111,
            "format": lookup_generator({
                0: "Normal electrode input",
                1: "Input shorted",
                2: "BIAS measurements",
                3: "Supply measurement",
                4: "Temperature sensor",
                5: "Test signal",
                6: "BIAS drive P",
                7: "BIAS drive N",
            })
        }
        REGISTER_MAP["BIASP" + str(i+1)] = {
            "address": 0x0D,
            "mask": 1 << i,
            "format": boolean_generator("OFF", "ON")
        }
        REGISTER_MAP["BIASN" + str(i+1)] = {
            "address": 0x0E,
            "mask": 1 << i,
            "format": boolean_generator("OFF", "ON")
        }
    
    LIST = [_ for _ in REGISTER_MAP]
    
    def __init__(self, spi, chip_select):
        self.spi = spi
        self.chip_select = chip_select
        
    def get_register_info(self, reg_name):
        try:
            return self.REGISTER_MAP[reg_name]
        except KeyError:
             raise Register.RegistNotExist("No such register")
    
    def __getattr__(self, attr):
        try:
            register = self.get_register_info(attr)
            command = bytearray(b'\x11\x20\x00\x00')
            command[1] |= register["address"]
            # Stop read data continuously mode 0x11
            # read register (0x20|address, 0x00, 0x00)
            self.chip_select.write(0)
            result = self.spi.write(command)[3]
            self.chip_select.write(1)
            return register["format"](result & register["mask"])
        except Register.RegistNotExist:
            raise AttributeError

    def __setattr__(self, attr, value):
        try:
            register = self.get_register_info(attr)
            command = bytearray(b'\x11\x20\x00\x00')
            command[1] |= register["address"]
            # Stop read data continuously mode 0x11
            # read register (0x20|address, 0x00, 0x00)
            self.chip_select.write(0)
            result = self.spi.write(command)[3]
            if isinstance(value, bool):
                if value:
                    result |= register["mask"]
                else:
                    result &= register["mask"]^0xFF
            elif isinstance(value, int):
                # set bits 1 to result
                result |= value & register["mask"]
                # set bits 0 to result
                result &= value | (register["mask"]^0xFF)
            else:
                raise TypeError("value must be an instance of int or bool.")
            command = bytearray(b'\x40\x00\x00')
            # write register (0x40|address, 0x00, value)
            command[0] = 0x40 + register["address"]
            command[2] |= result
            self.spi.write(command)
            self.chip_select.write(1)
        except Register.RegistNotExist:
            object.__setattr__(self, attr, value)
    
    def help(self, reg_name):
        # print register avalible choices
        register = self.get_register_info(reg_name)
        for key, value in register['format'].table.items():
            print key, ": ", value
