import os
import subprocess
from subprocess import Popen, PIPE, STDOUT
import time
import sys
# import shutil
import ftplib
import signal # signal.signal(signal.SIGCHLD, signal.SIG_IGN) to properly terminate zombie child process

# custom module
import linuxutil
import btcmdresptag
# import btcommander

# import uploadfile

# import util

# import json

# import om2m.om2m_ae_client

import logging

from multiprocessing.connection import Listener, Client # for interprocess


# from uploadfile import SftpUploadCallback

# reference to subprocess.POpen after starting LabRecorderCLI
processLabRecorderCLI = None

class Edison(object):
    def setBt(self, bt):
        self.bt = bt
        
    def setConfig(self, config):
        self.config = config
    
    def __init__(self):
    # self.counter = 0
    # self.server_sock = bt
        # self.config = config
        # self.bt = bt
        # self.btcmd = btcommander.BluetoothCommander(bt)
    
    # Set logging verbosity, default is WARNING
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)  
    
    # def __init__(self, bt, config):
        # self.counter = 0
        # """Initialize Edison object"""
        # self.server_sock = bt
        # self.config = config
        # self.btcmd = btcommander.BluetoothCommander(bt)
        
        # Set logging verbosity, default is WARNING
        # logging.basicConfig(level=logging.INFO)
        # self.logger = logging.getLogger(__name__)  
        
    def startLabRecorderCLI(self, args):       
        PROCESS_NAME = "LabRecorderCLI"
        print("Checking whether process=[%s] is already running!" % PROCESS_NAME)
        if linuxutil.checkIfProcessRunning(PROCESS_NAME):
            print("Oh No! It is already running, killing it now...")
            if linuxutil.killProcess(PROCESS_NAME): # failed to kill ads1299-edison process
                print(PROCESS_NAME + " killed successfully!")
            else:
                msg = "Failed to kill " + PROCESS_NAME
                print(msg)
                # self.btcmd.sendCommandResponseFailure(btcmdresptag.BluetoothCommandResponse.START_ADS1299_PROGRAM, msg)
                                                      
        print("Forking a child process to run the LabRecorderCLI program...")
        pid = os.fork()

        if pid:  # parent 
            signal.signal(signal.SIGCHLD, signal.SIG_IGN)
            pass
                
        else:  # child
            print("CHILD: running program...")
            argsTokens = args.split(';')
            print(argsTokens)
            
            argsTokens2 = argsTokens[0].split(' ')
            print(argsTokens2)
            
            # example of argsTokens2: 
            # ['-r', '500', '-o', 'none', '-f', 'eeglog-1604724876136', '-O', 'csv', '-s', '-1', '-c', 'nGoggle_G4_N1_4B5N6_8_500sps.json', '-A', '-S', 'lslmqtt', '-d', 'ascii', '-u', '100', '-D', '10', '-T', 'eeg', '-H', '127.0.0.1', '-o', 'none']

                # self.server_sock.send("%s:success;\r\n" % btcmdresptag.BluetoothCommandResponse.START_ADS1299_PROGRAM)
            # self.btcmd.sendCommandResponseSuccess(btcmdresptag.BluetoothCommandResponse.START_ADS1299_PROGRAM, 'Started ads1299-edison process successfully')
            
            # print('Sending reply back to client...')
            # self.bt.send_tx("%s:%s;%s;\r\n" % (btcmdresptag.BluetoothCommandResponse.START_ADS1299_PROGRAM, 'success', 'Started ads1299-edison process successfully') )
            
            # check if dir exist
            if not os.path.isdir(os.path.dirname(argsTokens2[5])):
                print(os.path.dirname(argsTokens2[5]) + " not found, creating it now!")
                os.makedirs(argsTokens2[5])
            
            processLabRecorderCLI = Popen( [self.config['app_path'] + "/LabRecorderCLI", argsTokens2[5]+".xdf", '\'type=\"EEG\" and name=\"NuPod-imx8\"\'', '\'type=\"Markers\" and name=\"mfSSVEPMarkerStream\"\''], stdout=PIPE, stdin=PIPE, stderr=STDOUT)   

            # processLabRecorderCLI = Popen( [self.config['app_path'] + "/LabRecorderCLI", argsTokens2[5]+".xdf", '\'type=\"EEG\" and name=\"NuPod-imx8\"\''], stdout=PIPE, stdin=PIPE, stderr=STDOUT)

            # cmd = self.config['app_path'] + "/LabRecorderCLI " + argsTokens2[5] + ".xdf" + '\'type=\"EEG\" and name=\"NuPod-imx8\"\' \'type=\"Markers\" and name=\"mfSSVEPMarkerStream\"\''
            # print("exec: " + cmd)
            # result = subprocess.call(cmd, shell=True)

            # example command:
            # LabRecorderCLI foo.xdf 'type="Markers" and name="mfSSVEPMarkerStream"' 'type="EEG" and name="NuPod-imx8"'
            

            print("Process opened, now starting IPC server on localhost:6000!")
            
            # start IPC server
            address = ('localhost', 6000)     # family is deduced to be 'AF_INET'
            listener = Listener(address, authkey='secret password'.encode())
            conn = listener.accept()
            print('connection accepted from {}'.format(listener.last_accepted))
            while True:
                msg = conn.recv()
                # do something with msg
                if (msg == 'close'):
                    # close LabRecorderCLI normally
                    print("Sending p.communicate to LabRecorderCLI...")
                    processLabRecorderCLI.communicate()
                    # print(grep_stdout.decode())
                    
                    msg = "File saved to " + argsTokens2[5] + ".xdf"
                    self.bt.send_tx("%s:%s;%s;\r\n" % (btcmdresptag.BluetoothCommandResponse.STOP_LABRECORDERCLI_PROGRAM, 'success', msg) )

                    conn.close()
                    break
            listener.close()            
            
            print("LabRecorderCLI exit normally!")
            print("Exit Child!")
            
            
            # cmd = self.config['app_path'] + "/LabRecorderCLI " + argsTokens2[5] + ".xdf \'type=\"EEG\"\'"
            # print("exec: " + cmd)
            # result = subprocess.call(cmd, shell=True)
            
            # IMPORTANT to exit the forked process
            # print("Exit child")
            # self.logger.debug("Exit child...")
            # os._exit(0)    

    def stopLabRecorderCLI(self):
        print("Sending p.communicate to LabRecorder process...")
        processLabRecorderCLI.communicate()
        # killChildProcesses(pid, signal.SIGTERM)
        # if linuxutil.killProcess('LabRecorderCLI'):
            # msg = "No LabRecorderCLI program is currently running! Please start it first!"
            # print(msg)
            # self.btcmd.sendCommandResponseFailure(btcmdresptag.BluetoothCommandResponse.STOP_ADS1299_PROGRAM, msg)
    
        # else: 
            # msg = "LabRecorderCLI program exit successfully"
            # print(msg)
            # self.btcmd.sendCommandResponseSuccess(btcmdresptag.BluetoothCommandResponse.STOP_ADS1299_PROGRAM, msg)
                        
        
    def startAds1299Program(self, args):
        """Start ADS1299 program, ads1299-edison in the forked child process"""
        
        ADS1299EDISON_PROCESS_NAME = "ads1299-imx"
        print("Checking whether process=[%s] is already running!" % ADS1299EDISON_PROCESS_NAME)
        if linuxutil.checkIfProcessRunning(ADS1299EDISON_PROCESS_NAME):
            print("Oh No! It is already running, killing the running ads1299-edison process")
            if linuxutil.killProcess(ADS1299EDISON_PROCESS_NAME): # failed to kill ads1299-edison process
                print("Process ads1299-edison killed successfully!")

            else:
                msg = "Failed to kill ads1299-edison process!"
                print(msg)
                # self.btcmd.sendCommandResponseFailure(btcmdresptag.BluetoothCommandResponse.START_ADS1299_PROGRAM, msg)
                # return            
                                                      
        print("Forking a child process to run the ads1299-edison program...")
        pid = os.fork()

        if pid:  # parent 
            signal.signal(signal.SIGCHLD, signal.SIG_IGN)
            pass
                
        else:  # child
            print("CHILD: running program...")
            argsTokens = args.split(';')
            print(argsTokens)
                # self.server_sock.send("%s:success;\r\n" % btcmdresptag.BluetoothCommandResponse.START_ADS1299_PROGRAM)
            # self.btcmd.sendCommandResponseSuccess(btcmdresptag.BluetoothCommandResponse.START_ADS1299_PROGRAM, 'Started ads1299-edison process successfully')
            
            print('Sending reply back to client...')
            self.bt.send_tx("%s:%s;%s;\r\n" % (btcmdresptag.BluetoothCommandResponse.START_ADS1299_PROGRAM, 'success', 'Started ads1299-imx process successfully') )

            cmd = self.config['app_path'] + "/ads1299-imx " + argsTokens[0];
            print("exec: " + cmd)
            result = subprocess.call(cmd, shell=True)

            if result:
                msg = "ADS1299 program stopped abnormally"
                self.logger.warning(msg)
                # self.btcmd.sendCommandResponseFailure(btcmdresptag.BluetoothCommandResponse.STOP_ADS1299_PROGRAM, msg)

            else: # process exit normally
                msg = "ADS1299 program stopped successfully!"
                self.logger.info(msg)
                # self.btcmd.sendCommandResponseSuccess(btcmdresptag.BluetoothCommandResponse.STOP_ADS1299_PROGRAM, msg)

            # IMPORTANT to exit the forked process
            self.logger.debug("Exit child...")
            os._exit(0)
            
    def stopAds1299Program(self):
        # stop labrecordercli if any
        if linuxutil.checkIfProcessRunning("LabRecorderCLI"):
            print("Found existing LabRecordingCLI, send IPC to stop it normally")
            address = ('localhost', 6000)
            conn = Client(address, authkey='secret password'.encode())
            conn.send('close')
            # can also send arbitrary objects:
            # conn.send(['a', 2.5, None, int, sum])
            conn.close()

            print("LabRecorderCLI closed, next stopping ads1299 program")

        PROCESS_NAME = "ads1299-imx"
        if linuxutil.checkIfProcessRunning(PROCESS_NAME):        
            print(PROCESS_NAME + " found! Sending SIGTERM to " + PROCESS_NAME + " process...")
            # killChildProcesses(pid, signal.SIGTERM)
            if linuxutil.killProcess(PROCESS_NAME):
                msg = PROCESS_NAME + " exit successfully"
                print(msg)
    #             self.btcmd.sendCommandResponseSuccess(btcmdresptag.BluetoothCommandResponse.STOP_ADS1299_PROGRAM, msg)
                self.bt.send_tx("%s:%s;%s;\r\n" % (btcmdresptag.BluetoothCommandResponse.STOP_ADS1299_PROGRAM, 'success', 'Stopped ads1299-imx program successfully') )

            else:
                msg = "Failed to kill process=" + PROCESS_NAME
                print(msg)
    #             self.btcmd.sendCommandResponseFailure(btcmdresptag.BluetoothCommandResponse.STOP_ADS1299_PROGRAM, msg)
                self.bt.send_tx("%s:%s;%s;\r\n" % (btcmdresptag.BluetoothCommandResponse.STOP_ADS1299_PROGRAM, 'failed', 'Failed to stop ads1299-imx program') )

        else: # not found
            msg = "There is no running recording program"
            print(msg)
            self.bt.send_tx("%s:%s;%s;\r\n" % (btcmdresptag.BluetoothCommandResponse.STOP_ADS1299_PROGRAM, 'failed', msg) )
        
        
        
    def startWestonCompositor(self):
        """ Return True if run successfully """
        PROCESS_NAME = "weston"

        if linuxutil.checkIfProcessRunning(PROCESS_NAME):
            print("Weston already running!")
            return True
        else:
            print("Cannot find weston, starting it now...")
            cmd = "sudo bash -c " + self.config['app_script_path'] + "/start-weston"
            print("exec: " + cmd)
            result = subprocess.call(cmd, shell=True)
            
            if result:
                return False
            else:
                return True
        

    def startVisualStimuli(self, args):

        # check if weston compositor is running
        startWestonCompositor()     
                                                      
        PROCESS_NAME = "visual stimuli"
        print("Forking a child process to run the stimuli program...")
        pid = os.fork()

        if pid:  # parent 
            signal.signal(signal.SIGCHLD, signal.SIG_IGN)
            pass
                
        else:  # child
            print("CHILD: running program...")
            argsTokens = args.split(';')
            print(argsTokens)
                # self.server_sock.send("%s:success;\r\n" % btcmdresptag.BluetoothCommandResponse.START_ADS1299_PROGRAM)
            # self.btcmd.sendCommandResponseSuccess(btcmdresptag.BluetoothCommandResponse.START_ADS1299_PROGRAM, 'Started ads1299-edison process successfully')
            
            print('Sending reply back to client...')
            self.bt.send_tx("%s:%s;%s;\r\n" % (btcmdresptag.BluetoothCommandResponse.START_VISUAL_STIMULI, 'success', 'Started visual stimuli program successfully') )

            cmd = "sudo XDG_RUNTIME_DIR=/tmp/xdg gst-launch-1.0 playbin3 uri=file:///home/debian/imx8-hbpulse-software/demovideo/mfssvep-quadrant.mp4 video-sink=waylandsink fullscreen=true flags=0x1"
            print("exec: " + cmd)
            result = subprocess.call(cmd, shell=True)

            if result:
                msg = "Visual stimuli program stopped abnormally"
                self.logger.warning(msg)
                # self.btcmd.sendCommandResponseFailure(btcmdresptag.BluetoothCommandResponse.STOP_ADS1299_PROGRAM, msg)

            else: # process exit normally
                msg = "Visual stimuli program stopped successfully!"
                self.logger.info(msg)
                # self.btcmd.sendCommandResponseSuccess(btcmdresptag.BluetoothCommandResponse.STOP_ADS1299_PROGRAM, msg)

            # IMPORTANT to exit the forked process
            self.logger.debug("Exit child...")
            os._exit(0)
            
    def stopVisualStimuli(self):
        PROCESS_NAME = "gst-launch-1.0"
        
        if linuxutil.checkIfProcessRunning(PROCESS_NAME):        
            print(PROCESS_NAME + " found! Sending SIGTERM to " + PROCESS_NAME + " process...")
            # killChildProcesses(pid, signal.SIGTERM)
            if linuxutil.killProcess(PROCESS_NAME):
                msg = PROCESS_NAME + " exit successfully"
                print(msg)
    #             self.btcmd.sendCommandResponseSuccess(btcmdresptag.BluetoothCommandResponse.STOP_ADS1299_PROGRAM, msg)
                self.bt.send_tx("%s:%s;%s;\r\n" % (btcmdresptag.BluetoothCommandResponse.STOP_VISUAL_STIMULI, 'success', 'Stopped visual stimuli program successfully') )

            else:
                msg = "Failed to kill process=" + PROCESS_NAME
                print(msg)
    #             self.btcmd.sendCommandResponseFailure(btcmdresptag.BluetoothCommandResponse.STOP_ADS1299_PROGRAM, msg)
                self.bt.send_tx("%s:%s;%s;\r\n" % (btcmdresptag.BluetoothCommandResponse.STOP_VISUAL_STIMULI, 'failed', 'Failed to stop visual stimuli program') )

        else: # not found
            msg = "There is no running visual stimuli program"
            print(msg)
            self.bt.send_tx("%s:%s;%s;\r\n" % (btcmdresptag.BluetoothCommandResponse.STOP_VISUAL_STIMULI, 'failed', msg) )

    