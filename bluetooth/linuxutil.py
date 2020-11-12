import subprocess
import psutil

# def checkProcess(process_name):
    # """Check whether process_name is already running"""
    # output = subprocess.check_output(['ps'])
    # if process_name in output:
        # return 0  # process is found!
    # return 1  


def killProcess(process_name):
    """Kill a process, return 0 if sucesss"""
    args = "killall " + process_name
    # return 0 if command is executed successfully
    result = subprocess.call(args, shell=True)
    # print("result=%d" % result)
    
    if result:
        return False
        
    else:
        return True # killed successfully

def checkIfProcessRunning(processName):
    '''
    Check if there is any running process that contains the given name processName.
    '''
    #Iterate over the all the running process
    for proc in psutil.process_iter():
        try:
            # Check if process name contains the given name string.
            if processName.lower() in proc.name().lower():
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return False  