import sys
import dbus, dbus.mainloop.glib
from gi.repository import GLib
from example_advertisement import Advertisement
from example_advertisement import register_ad_cb, register_ad_error_cb
from example_gatt_server import Service, Characteristic
from example_gatt_server import register_app_cb, register_app_error_cb

import threading
import logging

import time # for sleep
# ------------------------------------
# LSL
# used to check EEG type LSL stream before starting LabRecorderCLI
# from pylsl import StreamInlet, resolve_stream 

# MQTT
import paho.mqtt.client as mqtt

# From Edison Script
import json
import btcmdresptag
import edisonfunc

verbose = False

edison = edisonfunc.Edison()

client = mqtt.Client()

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("eeg")

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):

    # as string
    if (verbose):
        print("Rcvd from MQTT Broker: " + msg.topic+" "+str(msg.payload))
    sendMsgStr(str(msg.payload));
    
    # protobuf
    # print("msg len={}".format(len(msg.payload)))
    # sendMsgBytes(msg.payload)
    
def subscribing():
    client.on_message = on_message
    client.loop_forever()


# ------------------------------------

 
BLUEZ_SERVICE_NAME =           'org.bluez'
DBUS_OM_IFACE =                'org.freedesktop.DBus.ObjectManager'
LE_ADVERTISING_MANAGER_IFACE = 'org.bluez.LEAdvertisingManager1'
GATT_MANAGER_IFACE =           'org.bluez.GattManager1'
GATT_CHRC_IFACE =              'org.bluez.GattCharacteristic1'
UART_SERVICE_UUID =            '6e400001-b5a3-f393-e0a9-e50e24dcca9e'
UART_RX_CHARACTERISTIC_UUID =  '6e400002-b5a3-f393-e0a9-e50e24dcca9e'
UART_TX_CHARACTERISTIC_UUID =  '6e400003-b5a3-f393-e0a9-e50e24dcca9e'
UART_TX_CONTROL_CHARACTERISTIC_UUID =  '6e400004-b5a3-f393-e0a9-e50e24dcca9e'
LOCAL_NAME =                   'rpi-gatt-server'
mainloop = None

def sendMsgBytes(obj):
    if (verbose):
        print("sending back to client")
    s = obj
    global send
    # value = []
    # for c in s:
        # value.append(dbus.Byte(c))
    print(obj)
    send.PropertiesChanged(GATT_CHRC_IFACE, {'Value': value}, [])

def sendMsgStr(obj):
    if (verbose):
        print("sending back to client")
    s = obj
    global send
    value = []
    for c in s:
        value.append(dbus.Byte(c.encode()))
    if (verbose):
        print("msg len={}".format(len(value)))
    send.PropertiesChanged(GATT_CHRC_IFACE, {'Value': value}, [])
    
class ControlChannelTxCharacteristic(Characteristic):
    def __init__(self, bus, index, service):
        Characteristic.__init__(self, bus, index, UART_TX_CONTROL_CHARACTERISTIC_UUID,
                                ['notify'], service)
        self.notifying = False
        global sendControl
        sendControl = self
        GLib.io_add_watch(sys.stdin, GLib.IO_IN, self.on_console_input)
        
        edison.setBt(sendControl)
         
    def on_console_input(self, fd, condition):
        s = fd.readline()
        if s.isspace():
            pass
        else:
            self.send_tx(s)
        return True
 
    def send_tx(self, s):
        if not self.notifying:
            return
        value = []
        for c in s:
            value.append(dbus.Byte(c.encode()))
        self.PropertiesChanged(GATT_CHRC_IFACE, {'Value': value}, [])
 
    def StartNotify(self):
        if self.notifying:
            return
        self.notifying = True
 
    def StopNotify(self):
        if not self.notifying:
            return
        self.notifying = False    
 
class TxCharacteristic(Characteristic):
    def __init__(self, bus, index, service):
        Characteristic.__init__(self, bus, index, UART_TX_CHARACTERISTIC_UUID,
                                ['notify'], service)
        self.notifying = False
        global send
        send = self
        # GLib.io_add_watch(sys.stdin, GLib.IO_IN, self.on_console_input)
        
        edison.setBt(send)
         
    def on_console_input(self, fd, condition):
        s = fd.readline()
        if s.isspace():
            pass
        else:
            self.send_tx(s)
        return True
 
    def send_tx(self, s):
        if not self.notifying:
            return
        value = []
        for c in s:
            value.append(dbus.Byte(c.encode()))
        self.PropertiesChanged(GATT_CHRC_IFACE, {'Value': value}, [])
 
    def StartNotify(self):
        if self.notifying:
            return
        self.notifying = True
 
    def StopNotify(self):
        if not self.notifying:
            return
        self.notifying = False
 
class RxCharacteristic(Characteristic):
    def __init__(self, bus, index, service):
        Characteristic.__init__(self, bus, index, UART_RX_CHARACTERISTIC_UUID,
                                ['write'], service)
 
    """ This is called whenever GATT Client write to the RX_SERVICE_CHARACTERISTIC_UUID """
    def WriteValue(self, value, options):
        print('remote: {}'.format(bytearray(value).decode()))
        
       
        data = bytearray(value).decode()
        print("Received=" + data)
        
        ### Parse command 
        data = data.rstrip()

        # try:
        cmd = data.split('%')
        
        if len(cmd[0]) <= 0:
            print("Invalid command!")
                    
        
        else: # command exist
            # global edison

            print ("---------------------------------")
            print("Good! Command exist, cmd[0]={}".format(cmd[0]))
            print("cmd[1]={}".format(cmd[1]))
            if cmd[0] == btcmdresptag.BluetoothCommand.START_ADS1299_PROGRAM:
                print("Starting ADS1299CProgram from Python e...")
                edison.startAds1299Program(cmd[1]) 
    
                # start LabRecorderCLI for internal recording if [ -S = lslmqtt ]
                argsTokens = cmd[1].split(';')
                if argsTokens[0].find('lslmqtt') != -1:
                    print("Found lslqmtt in arg, wait 3s before starting LabRecorderCLI...")
                    
                    time.sleep(3)
                    print("Starting LabRecordingCLI...")
                    edison.startLabRecorderCLI(cmd[1])
                
            if cmd[0] == btcmdresptag.BluetoothCommand.STOP_ADS1299_PROGRAM:
                print("Stopping ADS1299CProgram from Python...")
                edison.stopAds1299Program()       

            # wrapper function?
            if cmd[0] == btcmdresptag.BluetoothCommand.START_EXPERIMENT:
                pass
                # print("1. Starting ADS1299CProgram from Python...")
                # edison.startAds1299Program(cmd[1])                  
                
                # print("2. StartingLabRecorderCLI...")
                # edison.startLabRecorderCLI(cmd[1])
                
                # print("3. Start Visual Stimuli")
                # edison.startVisualStimuli(cmd[1])

            if cmd[0] == btcmdresptag.BluetoothCommand.START_VISUAL_STIMULI:
                print("Start Visual Stimuli!")
                edison.startVisualStimuli(cmd[1])
                
                # send mqtt msg to SendMarkerString.py
                
            if cmd[0] == btcmdresptag.BluetoothCommand.STOP_VISUAL_STIMULI:
                print("Stop Visual Stimuli!")
                edison.stopVisualStimuli()
                
            else:
                print("Unknown command!")
            
            # if val == "Start":
                # print("Starting ADS1299 service!")
                # self.sends("ADS1299 started successfully!")            
        # except:
            # print("oops! Invalid command!")
            
        
     
            
    def sends(self, obj):
        print("sending back to client")
        s = obj
        global send
        value = []
        for c in s:
            value.append(dbus.Byte(c.encode()))
        send.PropertiesChanged(GATT_CHRC_IFACE, {'Value': value}, [])
        
 
class UartService(Service):
    def __init__(self, bus, index):
        Service.__init__(self, bus, index, UART_SERVICE_UUID, True)
        self.add_characteristic(TxCharacteristic(bus, 0, self))
        self.add_characteristic(RxCharacteristic(bus, 1, self))
        self.add_characteristic(ControlChannelTxCharacteristic(bus, 2, self))
 
class Application(dbus.service.Object):
    def __init__(self, bus):
        self.path = '/'
        self.services = []
        dbus.service.Object.__init__(self, bus, self.path)
 
    def get_path(self):
        return dbus.ObjectPath(self.path)
 
    def add_service(self, service):
        self.services.append(service)
 
    @dbus.service.method(DBUS_OM_IFACE, out_signature='a{oa{sa{sv}}}')
    def GetManagedObjects(self):
        response = {}
        for service in self.services:
            response[service.get_path()] = service.get_properties()
            chrcs = service.get_characteristics()
            for chrc in chrcs:
                response[chrc.get_path()] = chrc.get_properties()
        return response
 
class UartApplication(Application):
    def __init__(self, bus):
        Application.__init__(self, bus)
        self.add_service(UartService(bus, 0))
 
class UartAdvertisement(Advertisement):
    def __init__(self, bus, index):
        Advertisement.__init__(self, bus, index, 'peripheral')
        self.add_service_uuid(UART_SERVICE_UUID)
        self.add_local_name(LOCAL_NAME)
        self.include_tx_power = True
 
def find_adapter(bus):
    remote_om = dbus.Interface(bus.get_object(BLUEZ_SERVICE_NAME, '/'),
                               DBUS_OM_IFACE)
    objects = remote_om.GetManagedObjects()
    for o, props in objects.items():
        if LE_ADVERTISING_MANAGER_IFACE in props and GATT_MANAGER_IFACE in props:
            return o
        print('Skip adapter:', o)
    return None
 
def main():
    # Set logging verbosity, default is WARNING
    logging.basicConfig(level=logging.DEBUG)
    global logger 
    logger = logging.getLogger(__name__)

    global mainloop
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    bus = dbus.SystemBus()
    adapter = find_adapter(bus)
    if not adapter:
        print('BLE adapter not found')
        return
 
    service_manager = dbus.Interface(
                                bus.get_object(BLUEZ_SERVICE_NAME, adapter),
                                GATT_MANAGER_IFACE)
    ad_manager = dbus.Interface(bus.get_object(BLUEZ_SERVICE_NAME, adapter),
                                LE_ADVERTISING_MANAGER_IFACE)
 
    app = UartApplication(bus)
    adv = UartAdvertisement(bus, 0)
 
    mainloop = GLib.MainLoop()
 
    service_manager.RegisterApplication(app.get_path(), {},
                                        reply_handler=register_app_cb,
                                        error_handler=register_app_error_cb)
    ad_manager.RegisterAdvertisement(adv.get_path(), {},
                                     reply_handler=register_ad_cb,
                                     error_handler=register_ad_error_cb)
    try:
        print("Connecting to MQTT client...")
        client.on_connect = on_connect
        client.on_message = on_message

        client.connect("localhost", 1883, 60)
        
        sub=threading.Thread(target=subscribing)
        sub.start()

        # Blocking call that processes network traffic, dispatches callbacks and
        # handles reconnecting.
        # Other loop*() functions are available that give a threaded interface and a
        # manual interface.
        # client.loop_forever()   
        
   
        print("==============================================")
        print("Bootstraping...")
        print("==============================================")
        print("Reading program configuration from config.json")
        with open('config.json', 'r') as f:
            config = json.load(f)        

        APP_ROOT = config['app_root']
        APP_PATH = APP_ROOT + '/' + config['app_dir']
        APP_CONFIG_PATH = APP_ROOT + '/' + config['app_config_dir']
        RECORDING_FILE_HOME = APP_ROOT + '/' + config['app_recording_data_dir']
        APP_SCRIPT_PATH = APP_ROOT + '/' + config['app_scripts_dir']
        TOOL_PATH = APP_ROOT + '/' + config['tool_dir']
        
        global myConfig # assign myConfig to Edison instance once a client is connected in the main loop
        myConfig = {'app_root': APP_ROOT,
                    'app_path': APP_PATH,
                    'app_config_path': APP_CONFIG_PATH,
                    'recording_file_home': RECORDING_FILE_HOME,
                    'app_script_path': APP_SCRIPT_PATH,
                    'tool_path' : TOOL_PATH}

        print("Application Root: %s" % APP_ROOT)
        print("Application Script Path: %s" % APP_SCRIPT_PATH)
        print("Tool Path: %s" % TOOL_PATH)
        print("ADS1299 Application Path: %s" % APP_PATH) 
        print("ADS1299 Application Config Path: %s" % APP_CONFIG_PATH)
        print("ADS1299 Recording Data Path: %s" % RECORDING_FILE_HOME)
        print("==============================================")
        logger.info("Bootstrap complete!")
        logger.info("Waiting for Bluetooth LE GATT client connection...")        
        
        logger.info("Creating new Edison instance...")
        # global edison 
        # global send
        # edison = edisonfunc.Edison(myConfig)
        # edison = edisonfunc.Edison()
        edison.setConfig(myConfig)
        
        ### --- END OF BOOTSTRAP        
        

        logger.info("Starting weston compositor..")
        if edison.startWestonCompositor():
           logger.info("Starting Weston: OK")
            
        else:
            logger.info("Starting Weston: FAILED")

        logger.info("BT mainloop.run()")
        mainloop.run()
     
        
    

    except KeyboardInterrupt:
        adv.Release()
 
if __name__ == '__main__':
    main()
    