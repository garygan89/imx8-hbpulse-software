"""Example program to demonstrate how to send string-valued markers into LSL."""

import random
import time
import threading
import subprocess

from pylsl import StreamInfo, StreamOutlet

# MQTT
import paho.mqtt.client as mqtt
client = mqtt.Client()
TOPIC = "visualstimuli"

LSL_OUTLET_STREAM_NAME = 'mfSSVEPMarkerStream'

# LSL
# first create a new stream info (here we set the name to MyMarkerStream,
# the content-type to Markers, 1 channel, irregular sampling rate,
# and string-valued data) The last value would be the locally unique
# identifier for the stream as far as available, e.g.
# program-scriptname-subjectnumber (you could also omit it but interrupted
# connections wouldn't auto-recover). The important part is that the
# content-type is set to 'Markers', because then other programs will know how
#  to interpret the content
info = StreamInfo(LSL_OUTLET_STREAM_NAME, 'Markers', 1, 0, 'string', 'myuidw43536')

# next make an outlet
outlet = StreamOutlet(info)

print("Creating LSL outlet, stream name=" + LSL_OUTLET_STREAM_NAME)

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    print("Subscribing to topic={}".format(TOPIC))
    client.subscribe(TOPIC)
    
    print("Waiting for command...")

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):

    # as string
    print(msg.topic+" "+str(msg.payload))
    # sendMsgStr(str(msg.payload));
    
    msgStr = str(msg.payload, 'utf-8')
    print(msgStr)
    if msgStr == "start":
        print("Starting Visual Stimuli")
        startVisualStimuli()
        
    elif msgStr == "stop":
        print("Stopping Visual Stimuli")
        stopVisualStimuli()
        
    else:
        print("Unknown command!")
        
    
    # protobuf
    # print("msg len={}".format(len(msg.payload)))
    # sendMsgBytes(msg.payload)
    
def subscribing():
    client.on_message = on_message
    client.loop_forever()

def startVisualStimuli():
    # command.append("export WESTON_TTY=1")
    # command.append("XDG_RUNTIME_DIR=/tmp/xdg weston --tty=\"$WESTON_TTY\" --idle-time=0 --backend=drm-backend.so &")
    # command.append("export GST_GL_PLATFORM=egl GST_GL_API=gles2 GST_GL_WINDOW=gbm")
    # command.append("XDG_RUNTIME_DIR=/tmp/xdg gst-launch-1.0 playbin3 uri=http://distribution.bbb3d.renderfarming.net/video/mp4/big_buck_bunny_720p_surround.avi video-sink=waylandsink")   
    
    command = "XDG_RUNTIME_DIR=/tmp/xdg gst-launch-1.0 playbin3 uri=file:///home/debian/imx8-hbpulse-software/demovideo/mfssvep-quadrant.mp4 video-sink=waylandsink fullscreen=true flags=0x1"

    # send LSL marker stream
    outlet.push_sample(["11"])

    print("exec: {}".format(command))
    result = subprocess.call(command, shell=True)
        
def stopVisualStimuli():
    pass

def main():

    
    
    print("Connecting to MQTT client...")
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect("localhost", 1883, 60)
    
    sub=threading.Thread(target=subscribing)
    sub.start()
    

    # print("now sending markers...")
    # markernames = ['Test', 'Blah', 'Marker', 'XXX', 'Testtest', 'Test-1-2-3']
    # while True:
        # pick a sample to send an wait for a bit
        # print([random.choice(markernames)])
        # outlet.push_sample([random.choice(markernames)])
        # time.sleep(random.random() * 3)


if __name__ == '__main__':
    main()
