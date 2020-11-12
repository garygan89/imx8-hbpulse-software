import os
import subprocess
import time
import sys
import shutil
import ftplib
import signal # signal.signal(signal.SIGCHLD, signal.SIG_IGN) to properly terminate zombie child process

# custom module
import linuxutil
import btcmdresptag
import btcommander

import uploadfile

import util

import json

# import om2m.om2m_ae_client

import logging

from uploadfile import SftpUploadCallback

class Edison(object):
    
    def __init__(self, bt, config):
        self.counter = 0
        """Initialize Edison object"""
        self.server_sock = bt
        self.config = config
        self.btcmd = btcommander.BluetoothCommander(bt)
        
        # Set logging verbosity, default is WARNING
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)  
    
    def getWifiInfo(self):
        """Get the IP Address and connected AP SSID"""
        self.address = self.getIpAddress()
        self.ssid = self.getConnectedApSSID()
        
        if (self.address == ''):
            self.address = "N/A"
            
        if (self.ssid == ''):
            self.ssid = "N/A"
        self.btcmd.sendCommandResponse(btcmdresptag.BluetoothCommandResponse.WIFI_INFO, "%s;%s" % (self.address, self.ssid) )
    
    
    def getIpAddress(self):
        address = os.popen(
            "ifconfig | grep -A1 'wlan0' | grep 'inet'| awk -F' ' '{ print $2 }' | awk -F':' '{ print $2 }'").read().rstrip()
        print("IP address=" + address)
        return address
        # server_sock.send("ip_address:" + address + ";\r\n")
    
    
    def getConnectedApSSID(self):
        ssid = os.popen("iwgetid -r").read().rstrip()
        print("Connected AP SSID=" + ssid)
        return ssid
    
    
    def startAds1299Program(self, args):
        """Start ADS1299 program, ads1299-edison in the forked child process"""
        
        ADS1299EDISON_PROCESS_NAME = "ads1299-edison"
        print("Checking whether process=[%s] is already running!" % ADS1299EDISON_PROCESS_NAME)
        if linuxutil.checkProcess(ADS1299EDISON_PROCESS_NAME) == 0:
            print("Oh No! It is already running, killing the running ads1299-edison process")
            if linuxutil.killProcess(ADS1299EDISON_PROCESS_NAME): # failed to kill ads1299-edison process
                msg = "Failed to kill ads1299-edison process!"
                print(msg)
                self.btcmd.sendCommandResponseFailure(btcmdresptag.BluetoothCommandResponse.START_ADS1299_PROGRAM, msg)
                return
            else:
                print("Process ads1299-edison killed successfully!")
                                                      
        print("Forking a child process to run the ads1299-edison program...")
        pid = os.fork()
    
        if pid:  # parent 
            signal.signal(signal.SIGCHLD, signal.SIG_IGN)
            pass
                
        else:  # child
            print("CHILD: running program...")
            argsTokens = args.split(';')
            print(argsTokens)
#             self.server_sock.send("%s:success;\r\n" % btcmdresptag.BluetoothCommandResponse.START_ADS1299_PROGRAM)
            self.btcmd.sendCommandResponseSuccess(btcmdresptag.BluetoothCommandResponse.START_ADS1299_PROGRAM, 'Started ads1299-edison process successfully')

            cmd = self.config['app_path'] + "/ads1299-edison " + argsTokens[0];
            print("exec: " + cmd)
            result = subprocess.call(cmd, shell=True)
    
            if result:
                msg = "ADS1299 program stopped abnormally"
                self.logger.warning(msg)
                self.btcmd.sendCommandResponseFailure(btcmdresptag.BluetoothCommandResponse.STOP_ADS1299_PROGRAM, msg)

            else: # process exit normally
                msg = "ADS1299 program stopped successfully!"
                self.logger.info(msg)
                self.btcmd.sendCommandResponseSuccess(btcmdresptag.BluetoothCommandResponse.STOP_ADS1299_PROGRAM, msg)
    
            # IMPORTANT to exit the forked process
            self.logger.debug("Exit child...")
            os._exit(0)
            
            
    def stopAds1299Program(self):
        print("sending SIGTERM to ads1299 process...")
        # killChildProcesses(pid, signal.SIGTERM)
        if linuxutil.killProcess('ads1299-edison'):
            msg = "No ads1299-edison program is currently running! Please start it first!"
            print(msg)
#             self.btcmd.sendCommandResponseFailure(btcmdresptag.BluetoothCommandResponse.STOP_ADS1299_PROGRAM, msg)
    
        else: 
            msg = "ads1299-edison program exit successfully"
            print(msg)
#             self.btcmd.sendCommandResponseSuccess(btcmdresptag.BluetoothCommandResponse.STOP_ADS1299_PROGRAM, msg)

    # --------------------------------------------------------------------- Create record metadata
    def createRecordMetadata(self, args):
        print("Received JSON data: %s" % args)
        
        try:
            recordMetadataJson = json.loads(args)
        except Exception as e:
            print(e)
            msg = "Record metadata creation failed!"
            self.btcmd.sendCommandResponseFailure(btcmdresptag.BluetoothCommandResponse.CREATE_RECORD_METADATA, msg)
            sys.stdout.write("Failed to create ngmeta!\n")
            return


#         rawFilePath = recordMetadataJson['record']['recorded_data']['access_method_sftp']['locator']
        rawFilePath = recordMetadataJson['record']['recorded_data']['local_locator']
        print("rawfilepath = %s" % rawFilePath)
        
        parentDir = os.path.dirname(rawFilePath)
        print("parent dir = %s" % parentDir)
        
        baseNameWithExt = os.path.basename(rawFilePath)
        baseNameWithoutExt = os.path.splitext(baseNameWithExt)[0]
        
        recordMetadataFilePath = os.path.join(parentDir, baseNameWithoutExt + ".ngmeta")
        
        # replace sftp://hostname/homefolder with /media/sdcard
#         print("Reading program configuration from device_settings.json")
#         with open('/media/sdcard/configs/device_settings.json', 'r') as f:
#             device_config = json.load(f)
#             
#         sftp_hostname_homefolder = "sftp://" + device_config['sftp_conf']['sftp_hostname'] + ":" + device_config['sftp_conf']['sftp_recording_files_dir'] + "/"    
#         print("SFTP hostname homefolder: %s" % sftp_hostname_homefolder)
        
        # recordMetadataFilePath = recordMetadataFilePath.replace(sftp_hostname_homefolder, "/media/sdcard/logs/")
        
        print("Writing to: %s" % recordMetadataFilePath)
        with open(recordMetadataFilePath, 'w') as outfile:
            json.dump(recordMetadataJson, outfile, indent=4)
            
            msg = "Record metadata created successfully!"
            self.btcmd.sendCommandResponseSuccess(btcmdresptag.BluetoothCommandResponse.CREATE_RECORD_METADATA, msg)
            
            self.counter += 1
            sys.stdout.write("%d\n" % self.counter)

            
            
    def createRecordMetadataORI(self, args):
        argsTokens = args.split(';')
        
    #     argsTokens[0] = recordFileName
    #     argsTokens[1] = subjectId
    #     argsTokens[2] = samplingRate
    #     argsTokens[3] = recordStartTime
    #     argsTokens[4] = recordEndTime
    #     argsTokens[5] = bluetoothStreamingStatus
    #     argsTokens[6] = configFileName
    #     argsTokens[7] = recordingLabel
    #     argsTokens[8] = locationName
    #     argsTokens[9] = rating
        
        cmd = self.config['app_path'] + "/createrecordmetadata-edison -f " + argsTokens[0] + " -i " + argsTokens[1] + " -r " + argsTokens[2] + " -S " + argsTokens[3] + " -E " + argsTokens[4] + " -b " + argsTokens[5] + " -c " + argsTokens[6] + " -L " + argsTokens[7] + " -l " + argsTokens[8] + " -R " + argsTokens[9]
        
        result = subprocess.call(cmd, shell=True)
        self.logger.debug('exec: ' + cmd)
         
        if result:
            msg = "Record metadata created failed!"
            self.logger.warning(msg)
            self.btcmd.sendCommandResponseFailure(btcmdresptag.BluetoothCommandResponse.CREATE_RECORD_METADATA, msg)
         
        else:
            msg = "Record metadata created successfully!"
            self.logger.info(msg)
            self.btcmd.sendCommandResponseSuccess(btcmdresptag.BluetoothCommandResponse.CREATE_RECORD_METADATA, msg)
            
# --------------------------------------------------------------------- Upload record metadata to BCI Ontology
    def uploadRecordMetadataToBCIOntology(self, args):
        argsTokens = args.split(';')
        recordMetadataFilePath = argsTokens[0]
        
        self.logger.debug("Record Metadata File Path = %s" % recordMetadataFilePath)
        
        om2mAeClient = om2m.om2m_ae_client.Om2mAeClient()
        try:
            om2mAeClient.uploadRecordMetadata(recordMetadataFilePath)
            msg = "Record metadata successfully uploaded to BCI ontology!"
            self.logger.info(msg)
            self.btcmd.sendCommandResponseSuccess(btcmdresptag.BluetoothCommandResponse.UPLOAD_RECORD_METADATA_TO_BCI_ONTOLOGY, msg)
            
        except Exception:
            msg = "Record metadata failed to upload to BCI ontology!"
            self.logger.warning(msg)
            self.btcmd.sendCommandResponseFailure(btcmdresptag.BluetoothCommandResponse.UPLOAD_RECORD_METADATA_TO_BCI_ONTOLOGY, msg)

        
        
        
            
# --------------------------------------------------------------------- Convert from .pb to other format
    def convertFileFormat(self, args):
        # args[0] = recording file name
        # args[1] = target file format
        
        recordingDataDir = self.config['app_root'] + '/' + self.config['app_recording_data_dir']
        inputFilePath = recordingDataDir + '/' + args[0]
        outputFilePath = recordingDataDir + '/' + args[0]
        targetFileFormat = args[1]
        
        if args[1] == 'json':
            outputFilePath += '.json'
        elif args[1] == 'xml':
            outputFilePath += '.xml'
        
        cmd = "%s/ngoggle-data-converter -i %s -o %s -t %s" % (self.config['tool_path'], inputFilePath, outputFilePath, targetFileFormat)
         
        result = subprocess.call(cmd, shell=True)
        print('exec: ' + cmd)
         
        if result:
            msg = "Failed to convert data!"
            print(msg)
            self.btcmd.sendCommandResponseFailure(btcmdresptag.BluetoothCommandResponse.CONVERT_DATA_FORMAT, msg)
         
        else:
            msg = "Data converted successfully"
            print(msg)
            self.btcmd.sendCommandResponseSuccess(btcmdresptag.BluetoothCommandResponse.CONVERT_DATA_FORMAT, msg)
                     
        
# --------------------------------------------------------------------- Save custom ADS1299 JSON config
    def saveAds1299HardwareConfigJson(self, args):
        ADS1299_HW_CONF_FILE_PATH = self.config['app_config_path'] + '/custom.json'
        ADS1299_HW_CONF_NO_LOFF_FILE_PATH = self.config['app_config_path'] + '/custom_noleadoff.json'
    
        try:
            print("Saving custom ADS1299 hardware config to %s" % ADS1299_HW_CONF_FILE_PATH)
            ads1299HwConfFile = open(ADS1299_HW_CONF_FILE_PATH, "w")
            ads1299HwConfFile.write(args)
            ads1299HwConfFile.close()
    
            print("Saving %s" % ADS1299_HW_CONF_NO_LOFF_FILE_PATH)
            shutil.copy2(ADS1299_HW_CONF_FILE_PATH, ADS1299_HW_CONF_NO_LOFF_FILE_PATH)
    
            msg = "ADS1299 custom hardware config JSON saved success!"
            print(msg)
            self.btcmd.sendCommandResponseSuccess(btcmdresptag.BluetoothCommandResponse.SAVE_ADS1299_HW_CONFIG_JSON, msg)
    
        except Exception as e:
            msg = "Failed to save ads1299 custom json config"
            print(msg)
            self.btcmd.sendCommandResponseFailed(btcmdresptag.BluetoothCommandResponse.SAVE_ADS1299_HW_CONFIG_JSON, msg)            
            
# --------------------------------------------------------------------- Sync NTP time
    def syncNtpTime(self, args):
        argsTokens = args.split(';')
        ntpServerIp = argsTokens[0]
        
        cmd = "sntp -s " + ntpServerIp
        
        try:
            print('exec: ' + cmd)
            result = subprocess.call(cmd, shell=True)
            
            if result:
                msg = "SNTP synced failed!"
                print(msg)
                self.btcmd.sendCommandResponseFailure(btcmdresptag.BluetoothCommandResponse.NTP_SYNC, msg)
                
            else:
                msg = "SNTP synced success!"
                print(msg)
                self.btcmd.sendCommandResponseSuccess(btcmdresptag.BluetoothCommandResponse.NTP_SYNC, msg)

        except Exception as e:
            print("error:" + e)  
            
    def deleteAllRecordingFiles(self):
        recording_file_path = self.config['recording_file_home']
        print("Listing all files in %s" % recording_file_path)
        files = os.listdir(recording_file_path)       
        
        for f in files:
            absFilepath = os.path.join(recording_file_path, f)
            print("Deleting file: %s" % absFilepath)
            os.remove(absFilepath)
            
    def getRecordingFileCount(self):
        recordingFilesDir = self.config['recording_file_home']
        print("Listing all files in %s recursively..." % recordingFilesDir)
#         files = os.listdir(recordingFilesDir)
#         totalFiles = len(files)

        totalFiles = sum([len(files) for r, d, files in os.walk(recordingFilesDir)])
        print("Total files: %d" % totalFiles)

        msg = "%s;" % totalFiles
        self.btcmd.sendCommandResponseSuccess(btcmdresptag.BluetoothCommandResponse.GET_ALL_RECORDING_FILE_COUNT, msg)

    def uploadAllFTP(self, args):
        argsTokens = args.split(';')
        print(argsTokens)
        
        #args[0] = ftp server ip
        #args[1] = ftp server port
        #args[2] = ftp server username
        #args[3] = ftp server password
        #args[4] = ftp server working directory
        #args[5] = delete file after upload 
        #args[6] = tls/ssl connection
        
        fileuploader = uploadfile.FileUploader()
        
        isTlsSslConnection = False
        if argsTokens[6] == 'true':
            isTlsSslConnection = True
        else:
            isTlsSslConnection = False
        
        isDeleteFileAfterUpload = False
        if argsTokens[5] == 'true':
            isDeleteFileAfterUpload = True
        else:
            isDeleteFileAfterUpload = False
          
        ftpLoginInfo = fileuploader.getFTPLoginInfo()
        ftpLoginInfo['ftp_server_hostname'] = argsTokens[0]
        ftpLoginInfo['ftp_server_port'] = argsTokens[1]
        ftpLoginInfo['ftp_server_login_username'] = argsTokens[2]
        ftpLoginInfo['ftp_server_login_password'] = argsTokens[3]
        
        targetDir = argsTokens[4]
        
        if isTlsSslConnection == False:
            try:
                print("Connecting to FTP server using Plain Text mode...")
                print("Logging in to FTP server: %s:%s, U=%s P=%s" % (argsTokens[0], argsTokens[1], argsTokens[2], argsTokens[3]))
                fileuploader.openConnectionFTP(ftpLoginInfo)
                
            except Exception as e:
                print(e)
                return
            
        else:
            try:
                print("Connecting to FTP server using TLS/SSL...")
                print("Logging in to FTP server: %s:%s, U=%s P=%s" % (argsTokens[0], argsTokens[1], argsTokens[2], argsTokens[3]))
                fileuploader.openConnectionFTPS(ftpLoginInfo)
            except Exception as e:
                print(e)
                return      
            
        # Changing FTP directory
        fileuploader.switchDirFTP(targetDir)
            
        path = self.config['recording_file_home']
        print("Listing all files in %s" % path)
        files = os.listdir(path)
        
        try:
            fileCount = 1
            totalFiles = len(files)
            for f in files:
                absFilepath = os.path.join(path, f)
                
                if os.path.isdir(absFilepath):
                    print("%s is dir! Creating dir: %s on FTP server..." % (absFilepath, os.path.basename(absFilepath)))
                    fileuploader.switchDirFTP(os.path.basename(absFilepath))
                    
                    # list the files in the dir
                    recordingSessionFiles = os.listdir(absFilepath)
                    for sfiles in recordingSessionFiles:
                        sfilesAbsFilepath = os.path.join(absFilepath, sfiles)
                        print("Uploading file: %s" % sfilesAbsFilepath)
                        fileuploader.uploadFileFTP(sfilesAbsFilepath)
                        
                        # Send the information of the current file count and total files remaining to upload
                        msg = "%s;%s;%s;" % (sfiles,fileCount,totalFiles)
                        self.btcmd.sendCommandResponseSuccess(btcmdresptag.BluetoothCommandResponse.UPLOAD_FTP_ALL, msg)
                        fileCount = fileCount + 1
                        
                        if isDeleteFileAfterUpload:
                            print("Deleting file: %s" % sfilesAbsFilepath)
                            os.remove(sfilesAbsFilepath)
                            
                    # switch back to base dir
                    fileuploader.switchDirFTP("..")
                    
                    if isDeleteFileAfterUpload:
                        print("Deleting dir: %s" % absFilepath)
                        os.rmdir(absFilepath)  
                                        
                    
                else:
                    print("Uploading file: %s" % absFilepath)
                    fileuploader.uploadFileFTP(absFilepath)
                    
                    # Send the information of the current file count and total files remaining to upload
                    msg = "%s;%s;%s;" % (f,fileCount,totalFiles)
                    self.btcmd.sendCommandResponseSuccess(btcmdresptag.BluetoothCommandResponse.UPLOAD_FTP_ALL, msg)
                    fileCount = fileCount + 1
                    
                    if isDeleteFileAfterUpload:
                        print("Deleting file: %s" % f)
                        os.remove(absFilepath)
            
        except:
            msg = "Upload FTP failed!"
            print(msg)
            self.btcmd.sendCommandResponseFailure(btcmdresptag.BluetoothCommandResponse.UPLOAD_FTP_ALL, msg)
            return        
                
        print("All files uploaded, quitting session...")
        try:
            fileuploader.closeFTPConnection()
        except Exception as e:
            print(e)
            

    class MySftpUploadCallback(SftpUploadCallback):
        def _init_(self):
#             print("_init_")
            self.curr_uploaded_file_idx = 0
            
#         def onUploadFile(self, filename):
#             print("MYSFTPUPLOADCALLBACK: UPLOADING: %s..." % filename)
# #             self.curr_uploaded_file_idx += 1
# #             msg = "%d;" % self.curr_uploaded_file_idx
# #             self.btcallback.sendCommandResponseSuccess(btcmdresptag.BluetoothCommandResponse.UPLOAD_SFTP_PROGRESS, "1;")
# #             try:
# #                 self.btcallback.sendCommandResponseSuccess(btcmdresptag.BluetoothCommandResponse.UPLOAD_SFTP_PROGRESS, "1")
# #             except Exception as e:
# #                 print(e)            


    def uploadAllSFTP(self, args):
        argsTokens = args.split(';')
        print(argsTokens)
        
        #args[0] = sftp server ip
        #args[1] = sftp server port
        #args[2] = sftp server username
        #args[3] = sftp server password
        #args[4] = sftp server working directory
        #args[5] = delete file after upload 
        
        fileuploader = uploadfile.FileUploader()
        
        isDeleteFileAfterUpload = False
        if argsTokens[5] == 'true':
            isDeleteFileAfterUpload = True
        else:
            isDeleteFileAfterUpload = False
          
        print("Getting SFTPLoginInfo...")
        sftpLoginInfo = fileuploader.getSFTPLoginInfo()
        sftpLoginInfo['sftp_server_hostname'] = argsTokens[0]
        sftpLoginInfo['sftp_server_port'] = argsTokens[1]
        sftpLoginInfo['sftp_server_login_username'] = argsTokens[2]
        sftpLoginInfo['sftp_server_login_password'] = argsTokens[3]
        
        targetDir = argsTokens[4]
        
        print("Opening SFTP connection...")
        try:
            fileuploader.openConnectionSFTP(sftpLoginInfo)
        except Exception as e:
            print(e)
            msg = "Authentication failed! Please check SFTP username and password is correct!"
            self.btcmd.sendCommandResponseFailure(btcmdresptag.BluetoothCommandResponse.UPLOAD_SFTP_ALL, msg)
            return
            
        path = self.config['recording_file_home']
        print("Listing all files in %s" % path)
        files = os.listdir(path)
        
        sftp_upload_callback = self.MySftpUploadCallback()
        sftp_upload_callback.setBtCallback(self.btcmd)
        
        try:
            fileCount = 1
            totalFiles = len(files)
            for f in files:
                absFilepath = os.path.join(path, f)
                fileuploader.uploadFileSFTP(sftp_upload_callback, absFilepath, targetDir)
                
                # Send the information of the current file count and total files remaining to upload
                msg = "%s;%s;%s;" % (f,fileCount,totalFiles)
                self.btcmd.sendCommandResponseSuccess(btcmdresptag.BluetoothCommandResponse.UPLOAD_SFTP_ALL, msg)
                fileCount = fileCount + 1
                
                if isDeleteFileAfterUpload:
                    if os.path.isfile(absFilepath):
                        print("Deleting file: %s" % absFilepath)
                        os.remove(absFilepath)
                    elif os.path.isdir(absFilepath):
                        print("Deleting folder: %s" % absFilepath)
                        shutil.rmtree(absFilepath)
            
        except:
            msg = "Upload FTP failed!"
            print(msg)
            self.btcmd.sendCommandResponseFailure(btcmdresptag.BluetoothCommandResponse.UPLOAD_SFTP_ALL, msg)
            return        
                
        print("All files uploaded, quitting session...")
        try:
            fileuploader.closeSFTPConnection()
        except Exception as e:
            print(e)        
       

            
    def uploadAllFTPOri(self, args):
        argsTokens = args.split(';')
        print(argsTokens)
        
        #args[0] = ftp server ip
        #args[1] = ftp server port
        #args[2] = ftp server username
        #args[3] = ftp server password
        #args[4] = ftp server working directory
        #args[5] = delete file after upload 
        #args[6] = tls/ssl connection
        
        isTlsSslConnection = False
        if argsTokens[6] == 'true':
            isTlsSslConnection = True
        else:
            isTlsSslConnection = False
        
        isDeleteFileAfterUpload = False
        if argsTokens[5] == 'true':
            isDeleteFileAfterUpload = True
        else:
            isDeleteFileAfterUpload = False
        

        if isTlsSslConnection == False:
            try:
                print("Connecting to FTP server using Plain Text mode...")
                print("Logging in to FTP server: %s:%s, U=%s P=%s" % (argsTokens[0], argsTokens[1], argsTokens[2], argsTokens[3]))
                session = ftplib.FTP(argsTokens[0], argsTokens[2], argsTokens[3])
                
            except:
                msg = "Session timeout"
                print(msg)
                self.btcmd.sendCommandResponseFailure(btcmdresptag.BluetoothCommandResponse.UPLOAD_FTP_ALL, msg)
                return
            
        else:
            try:
                print("Connecting to FTP server using TLS/SSL...")
                print("Logging in to FTP server: %s:%s, U=%s P=%s" % (argsTokens[0], argsTokens[1], argsTokens[2], argsTokens[3]))
                session = ftplib.FTP_TLS(argsTokens[0])
                session.login(argsTokens[2], argsTokens[3])
                session.prot_p() # switch to secure data connection.. IMPORTANT! Otherwise, only the user and password is encrypted and not all the file data.
            except:
                print("Error while connecting to FTP server!")
                return        

        try:
            print("Changing dir to " + argsTokens[4])
            session.cwd(argsTokens[4])
            
        except:
            print("Dir: %s doesn't exist, creating it now..." % argsTokens[4])
            session.mkd(argsTokens[4])
            session.cwd(argsTokens[4])
            
        path = self.config['recording_file_home']
        print("Listing all files in %s" % path)
        files = os.listdir(path)
        
        try:
            fileCount = 1
            totalFiles = len(files)
            for f in files:
                absFilepath = os.path.join(path, f)
                print("Uploading file: %s" % absFilepath)
                openFile = open(absFilepath, 'rb')
                session.storbinary('STOR ' + f, openFile)
                openFile.close()
                
                # Send the information of the current file count and total files remaining to upload
                msg = "%s;%s;%s;" % (f,fileCount,totalFiles)
                self.btcmd.sendCommandResponseSuccess(btcmdresptag.BluetoothCommandResponse.UPLOAD_FTP_ALL, msg)
                fileCount = fileCount + 1
                
                if isDeleteFileAfterUpload:
                    print("Deleting file: %s" % f)
                    os.remove(absFilepath)
                
            print("All files uploaded, quitting session...")
            session.quit()
            
        except:
            msg = "Upload FTP failed!"
            print(msg)
            self.btcmd.sendCommandResponseFailure(btcmdresptag.BluetoothCommandResponse.UPLOAD_FTP_ALL, msg)        
            
# --------------------------------------------------------------------- FTP Upload
    def uploadFTP(self, args):
        argsTokens = args.split(';')
        print(argsTokens)
    
        #args[0] = ftp server ip
        #args[1] = ftp server port
        #args[2] = ftp server username
        #args[3] = ftp server password
        #args[4] = ftp server working directory
        #args[5] = recording file name
        #args[6] = recording metadata file name
    
        # ftp = FTP(argsTokens[0], argsTokens[2], argsTokens[3])
        try:
            print("Logging in to FTP server %s:%s, U=%s P=%s" % (argsTokens[0], argsTokens[1], argsTokens[2], argsTokens[3]))
            
    #         session = ftplib.FTP(argsTokens[0] + ":" + argsTokens[1], argsTokens[2], argsTokens[3])
            session = ftplib.FTP(argsTokens[0], argsTokens[2], argsTokens[3])
            
            # ftp.login()
    
            # open the file
            recordingFile = self.config['recording_file_home'] + '/' + argsTokens[5]
            recordingMetadataFile = self.config['recording_file_home'] + '/' + argsTokens[6]
    #         file = open('/media/sdcard/app/ads1299-edison', 'rb')
    
            print("Opening recording file: %s" % recordingFile)
            file = open(recordingFile, 'rb')
            callback = self.handle
            blocksize = 1024
    
            # change the working directory
            
            print("Changing dir to " + argsTokens[4])
            session.cwd(argsTokens[4])
    
    #         session.storbinary('STOR ads1299-edison.bin', file)
    
            print("STOR file as " + argsTokens[5])
            session.storbinary('STOR ' + argsTokens[5], file)
            
            # Recording Metadata
            print("Opening recording metadata file: %s" % recordingMetadataFile)
            file = open(recordingMetadataFile, 'rb')
            
            print("STOR file as " + argsTokens[6])
            session.storbinary('STOR ' + argsTokens[6], file)        
    
            # ftp.storbinary('STOR ads1299-edisontest', file, callback, blocksize)
            file.close()
            session.quit()
    
            msg = "Upload FTP success!"
            print(msg)
            self.btcmd.sendCommandResponseSuccess(btcmdresptag.BluetoothCommandResponse.UPLOAD_FTP, msg)
            
        except:
            msg = "Upload FTP failed!"
            print(msg)
            self.btcmd.sendCommandResponseFailure(btcmdresptag.BluetoothCommandResponse.UPLOAD_FTP, msg)
    
    def handle(self, block):
        print('.')           
        
# --------------------------------------------------------------------- Start Webserver API
    def startWebserverAPI(self):
        cmd = "systemctl start ngoggle-control-api-webserver"
        result = subprocess.call(cmd, shell=True)
    
        if result:
            msg = "Webserver API failed to start!"
            print(msg)
            self.btcmd.sendCommandResponseFailure(btcmdresptag.BluetoothCommandResponse.START_WEBSERVER_API, msg)
    
        else:
            msg = "Webserver API started successfully!"
            print(msg)
            self.btcmd.sendCommandResponseSuccess(btcmdresptag.BluetoothCommandResponse.START_WEBSERVER_API, msg)
            
# --------------------------------------------------------------------- Stop Webserver API
    def stopWebserverAPI(self):
        cmd = "systemctl stop ngoggle-control-api-webserver"
        result = subprocess.call(cmd, shell=True)
    
        if result:
            msg = "Webserver API failed to stop!"
            print(msg)
            self.btcmd.sendCommandResponseFailure(btcmdresptag.BluetoothCommandResponse.STOP_WEBSERVER_API, msg)
    
        else:
            msg = "Webserver API stopped successfully!"
            print(msg)
            self.btcmd.sendCommandResponseSuccess(btcmdresptag.BluetoothCommandResponse.STOP_WEBSERVER_API, msg)            
                                
            
# --------------------------------------------------------------------- Start Webserver UI 
    def startWebserverUI(self):
        cmd = "systemctl start ngoggle-control-ui-webserver"
        result = subprocess.call(cmd, shell=True)
    
        if result:
            msg = "Webserver UI failed to start!"
            print(msg)
            self.btcmd.sendCommandResponseFailure(btcmdresptag.BluetoothCommandResponse.START_WEBSERVER_UI, msg)
    
        else:
            msg = "Webserver UI started successfully!"
            print(msg)
            self.btcmd.sendCommandResponseSuccess(btcmdresptag.BluetoothCommandResponse.START_WEBSERVER_UI, msg)
            
# --------------------------------------------------------------------- Stop Webserver UI
    def stopWebserverUI(self):
        cmd = "systemctl stop ngoggle-control-ui-webserver"
        result = subprocess.call(cmd, shell=True)
    
        if result:
            msg = "Webserver UI failed to stop!"
            print(msg)
            self.btcmd.sendCommandResponseFailure(btcmdresptag.BluetoothCommandResponse.STOP_WEBSERVER_UI, msg)
    
        else:
            msg = "Webserver UI stopped successfully!"
            print(msg)
            self.btcmd.sendCommandResponseSuccess(btcmdresptag.BluetoothCommandResponse.STOP_WEBSERVER_UI, msg)             
            
# --------------------------------------------------------------------- Stress test using Prime95
    def startStressTestPrime95(self):  
        print("Stress testing using mprime Prime95 program...")     
       # Execute the command and print the intermediary result immediately
        cmd = self.config['tool_path'] + "/prime95/mprime -t &"
        result = subprocess.call(cmd, shell=True)
    
        if result:
            msg = "Stress test failed to start!"
            print(msg)
            self.btcmd.sendCommandResponseFailure(btcmdresptag.BluetoothCommandResponse.START_STRESS_TEST_PRIME95, msg)
    
        else:
            msg = "Stress test successfully started!"
            print(msg)
            self.btcmd.sendCommandResponseSuccess(btcmdresptag.BluetoothCommandResponse.START_STRESS_TEST_PRIME95, msg)
            
# --------------------------------------------------------------------- Stress test using Prime95
    def stopStressTestPrime95(self):  
        print("Killing mprime process...")     
        if linuxutil.killProcess('mprime'):
            msg = "No mprime program is currently running! Please start it first!"
            print(msg)
            self.btcmd.sendCommandResponseFailure(btcmdresptag.BluetoothCommandResponse.STOP_STRESS_TEST_PRIME95, msg)
    
        else: 
            msg = "Stress test program exit successfully"
            print(msg)
            self.btcmd.sendCommandResponseSuccess(btcmdresptag.BluetoothCommandResponse.STOP_STRESS_TEST_PRIME95, msg)             
                         

# --------------------------------------------------------------------- Update program
    def updateProgram(self):
        print("Downloading update script from server...")
        
        # Execute the command and print the intermediary result immediately
        cmd = "sh " + self.config['app_script_path'] + "/program_update.sh"
        result = subprocess.call(cmd, shell=True)
    
        if result:
            msg = "Program update failed!"
            print(msg)
            self.btcmd.sendCommandResponseFailure(btcmdresptag.BluetoothCommandResponse.UPDATE_PROGRAM, msg)
    
        else:
            msg = "Program update success!"
            print(msg)
            version = subprocess.check_output("cat " + self.config['app_root'] + "/VERSION.txt", shell=True)
            print("Package Version=" + version)
            self.btcmd.sendCommandResponseSuccess(btcmdresptag.BluetoothCommandResponse.UPDATE_PROGRAM, version)
            
# --------------------------------------------------------------------- Reset WiFi Config
    def restoreFactorySettings(self):
        result = subprocess.call("cp /etc/wpa_supplicant/wpa_supplicant.conf.original /etc/wpa_supplicant/wpa_supplicant.conf", shell=True)
        if result:
            msg = "Restore factory settings failed"
            print(msg)
            self.btcmd.sendCommandResponseFailure(btcmdresptag.BluetoothCommandResponse.RESTORE_FACTORY_SETTINGS, msg)
        else:
            msg = "Restore factory settings success"
            print(msg)
            self.btcmd.sendCommandResponseSuccess(btcmdresptag.BluetoothCommandResponse.RESTORE_FACTORY_SETTINGS, msg)
            
# --------------------------------------------------------------------- Reboot
    def reboot(self):
        cmd = "reboot"
        result = subprocess.call(cmd, shell=True)
        print('exec: ' + cmd)
         
        if result:
            return False
        else:
            return True
        
# --------------------------------------------------------------------- Power off
    def powerOff(self):
        cmd = "poweroff"
        result = subprocess.call(cmd, shell=True)
        print('exec: ' + cmd)
         
        if result:
            return False
        else:
            return True                                 
                     