class BluetoothCommandResponse:
    """ A list of bluetooth command response tag sent back to nGoggle Android app
    """
    CONFIGURE_WIFI_SCANNING_AP = "configure_wifi_scanning_ap"
    CONFIGURE_WIFI_NETWORK_PASSWORD = "configure_wifi_network_password"
    CONFIGURE_WIFI_CHECK_NETWORK = "configure_wifi_check_network"
    CONFIGURE_WIFI_SET_NETWORK = "configure_wifi_set_network"
    
    WIFI_INFO = "wifi_info"
    
    START_ADS1299_PROGRAM = "start_ads1299_program"
    STOP_ADS1299_PROGRAM = "stop_ads1299_program"
    CREATE_RECORD_METADATA = "create_record_metadata"
    SAVE_ADS1299_HW_CONFIG_JSON = "ads1299_hw_conf_file_save"
    
    CONVERT_DATA_FORMAT = "convert_data_format"
    
    NTP_SYNC = "ntp_sync"
    UPLOAD_FTP = "upload_ftp"
    UPLOAD_FTP_ALL = "upload_ftp_all"
    UPLOAD_SFTP_ALL = "upload_sftp_all"
    UPLOAD_SFTP_PROGRESS = "upload_sftp_progress"
    
    UPDATE_PROGRAM = "update_program"
    
    DELETE_ALL_RECORDING_FILE = "delete_all_recording_file"
    
    GET_ALL_RECORDING_FILE_COUNT = "get_all_recording_file_count"

    
    START_WEBSERVER_API = "start_webserver_api"
    STOP_WEBSERVER_API = "stop_webserver_api"
    START_WEBSERVER_UI = "start_webserver_ui"
    STOP_WEBSERVER_UI = "stop_webserver_ui"
    
    UPLOAD_RECORD_METADATA_TO_BCI_ONTOLOGY = "upload_record_metadata_to_bci_ontology"

    
    START_STRESS_TEST_PRIME95 = "start_stress_test_prime95"
    STOP_STRESS_TEST_PRIME95 = "stop_stress_test_prime95"
    
    RESTORE_FACTORY_SETTINGS = "restore_factory_settings"
    
    START_VISUAL_STIMULI = "start_visual_stimuli"
    STOP_VISUAL_STIMULI = "stop_visual_stimuli"    
    
    STOP_LABRECORDERCLI_PROGRAM = "stop_labrecordercli_program"
    
class BluetoothCommand:
    """ A list of bluetooth command tag received from nGoggle Android app
    """
    START_ADS1299_PROGRAM = "startADS1299CProgram"
    STOP_ADS1299_PROGRAM = "stopADS1299CProgram"
    CONFIGURE_WIFI = "configureWifi"
    CONFIGURE_WIFI_CONNECT_AP = "connectWifiAp"
    CONFIGURE_WIFI_SET_AP_PASSWORD = "sendWifiApPassword"
    
    GET_WIFI_IP_ADDRESS = "getWifiIpAddress"
    GET_WIFI_INFO = "getWifiInfo"
    
    UPLOAD_FTP = "uploadRecordingFileFTP"
    
    UPLOAD_BATCH_FTP = "uploadBatchRecordingFileFTP"
    UPLOAD_BATCH_SFTP = "uploadBatchRecordingFileSFTP"
    
    DELETE_ALL_RECORDING_FILE = "deleteAllRecordingFiles"
    
    GET_ALL_RECORDING_FILE_COUNT = "getAllRecordingFilesCount"
    
    CONVERT_DATA_FORMAT = "convertDataFormat"
    
    UPDATE_PROGRAM = "updateProgram"
    RESTORE_FACTORY_SETTINGS = "restoreFactorySettings"
    
    CREATE_RECORD_METADATA = "createRecordMetadata"
    SAVE_ADS1299_HW_CONFIG_JSON = "saveAds1299HardwareConfigJson"
    
    START_WEBSERVER_API = "startWebserverApi"
    STOP_WEBSERVER_API = "stopWebserverApi"
    START_WEBSERVER_UI = "startWebserverUi"
    STOP_WEBSERVER_UI = "stopWebserverUi"
    
    UPLOAD_RECORD_METADATA_TO_BCI_ONTOLOGY = "uploadRecordMetadataToBciOntology"
    
    START_STRESS_TEST_PRIME95 = "startStressTestPrime95"
    STOP_STRESS_TEST_PRIME95 = "stopStressTestPrime95"
    
    REBOOT = "reboot"
    POWER_OFF = "powerOff"
    
    SYNC_NTP = "syncNtpTime"
    
    START_VISUAL_STIMULI = "startVisualStimuli"
    STOP_VISUAL_STIMULI = "stopVisualStimuli"
    
    # START_LSL_RECORDING = "startLslRecording"
    
    START_EXPERIMENT = "startExperiment"
    
    