#!/usr/bin/python
import mraa
from mraa import Gpio

def init_gpio(pin, dir=mraa.DIR_OUT_LOW, mode=mraa.MODE_STRONG):
    gpio = Gpio(pin)
    gpio.dir(dir)
    gpio.mode(mode)
    return gpio

def pause(msg=""):
    print(msg + ". Press Enter to continue...")
    try:
        a = input()
    except Exception:
        pass

def make_gpio(gpio, name):
    return {"gpio": gpio, "name": name}

def test(gpio_dir):
    gpio = gpio_dir["gpio"]
    name = gpio_dir["name"]
    gpio.write(0)
    pause("LED " + name + " is OFF")
    gpio.write(1)
    pause("LED " + name + " is ON")
    gpio.write(0)
  
red = make_gpio(init_gpio(48), "red")
blue = make_gpio(init_gpio(36), "blue")
test(red)
test(blue)
