#!/bin/bash
# A simple shell script to manage wifi using wpa_supplicant and udhcpc
# Last Update: Sep-07-2020
# By: Gary
# --------------------------------------------------------------------------------
black=$(tput setaf 0); red=$(tput setaf 1); green=$(tput setaf 2); yellow=$(tput setaf 3);
blue=$(tput setaf 4); magenta=$(tput setaf 5); cyan=$(tput setaf 6); white=$(tput setaf 7);
on_red=$(tput setab 1); on_green=$(tput setab 2); on_yellow=$(tput setab 3); on_blue=$(tput setab 4);
on_magenta=$(tput setab 5); on_cyan=$(tput setab 6); on_white=$(tput setab 7); bold=$(tput bold);
dim=$(tput dim); underline=$(tput smul); reset_underline=$(tput rmul); standout=$(tput smso);
reset_standout=$(tput rmso); normal=$(tput sgr0); alert=${white}${on_red}; title=${standout};
baihuangse=${white}${on_yellow}; bailanse=${white}${on_blue}; bailvse=${white}${on_green};
baiqingse=${white}${on_cyan}; baihongse=${white}${on_red}; baizise=${white}${on_magenta}; jiacu=${normal}${bold}
heibaise=${black}${on_white}; shanshuo=$(tput blink); wuguangbiao=$(tput civis); guangbiao=$(tput cnorm)
CW="${bold}${baihongse} ERROR ${jiacu}";ZY="${baihongse}${bold} ATTENTION ${jiacu}";JG="${baihongse}${bold} WARNING ${jiacu}"
sep="==============================================="
sep2="-------------------------"
# --------------------------------------------------------------------------------

# error code
declare -i ERROR_WPA_SUPPLICANT=1 # as int
declare -i ERROR_UDHCP=2

# path
WPA_SUPPLICANT_CONFIG_PATH='/etc/wpa_supplicant/wpa_supplicant-wlan0.conf' # active config used by wpa_supplicant
WPA_SUPPLICANT_DEFAULT_CONFIG_PATH='/etc/wpa_supplicant/wpa_supplicant-wlan0.conf.orig' # system default
WPA_SUPPLICANT_CONFIG_BACKUP_PATH='/etc/wpa_supplicant/wpa_supplicant-wlan0.conf.bak' # backup of user file

function _readinput() {
    local _resultvar=$1
    read input
    while [[ $input = "" ]]; do
        echo "Please check your input"
        read -r input
    done    
    
    eval $_resultvar="$input"
}

function _checkwpaconfigfile() {
    if [ ! -f $WPA_SUPPLICANT_CONFIG_PATH ]; then
        echo "${yellow}Unable to find config file, restoring from default config...${normal}"
        _restoredefaultwificonfig
    fi
}

function _configure_wifi() {
    echo "Enter access point name:"; _readinput ap_name   
    echo "Enter access point password:"; _readinput ap_pass
    echo "Access point name: " ${bold}$ap_name${normal}
    echo "Access point password: " ${bold}$ap_pass${normal}
    
    while [[ $ys = "" ]]; do
        echo "Is this correct (y/n)?" ; read yn
        case $yn in
            y | Y )
                break;;
            n | N )
                _askinput
                break;;
        esac
    done 
    
    # check config file
    _checkwpaconfigfile
    
    # generate passphrase
    sudo bash -c "wpa_passphrase $ap_name $ap_pass >> /etc/wpa_supplicant/wpa_supplicant-wlan0.conf"
    
    # connect to ap
    echo "Connecting to AP=$ap_name via wpa_supplicant..."
    sudo wpa_supplicant -B -i wlan0 -c /etc/wpa_supplicant/wpa_supplicant-wlan0.conf -D nl80211 
    
    if [ ! $? -eq 0 ]; then
        # exit $ERROR_WPA_SUPPLICANT
        _askinput
    fi
    
    # get ip from dhcp    
    echo "Getting IP from DHCP server..."
    sudo udhcpc -i wlan0
    
    if [ ! $? -eq 0 ]; then
        # exit $ERROR_UDHCP
        _askinput
    fi    
  
    # prompt to autostart service
    while [[ $ys = "" ]]; do
        echo "Do you want to autostart wifi service every time your system restart? (y/N):" ; read yn
        case $yn in
            y | Y )
                sudo systemctl enable wpa_supplicant@wlan0
                sudo systemctl enable dhclient@wlan0
                break;;
            n | N )
                break;;
        esac
    done     
    
    echo "Successfully configured wifi!"
    ip a
}

function _enableservicefile() {
    sudo systemctl enable wpa_supplicant@wlan0
    sudo systemctl enable dhclient@wlan0
}

function _disableservicefile() {
    sudo systemctl disable wpa_supplicant@wlan0
    sudo systemctl disable dhclient@wlan0
}

function _showwificonfig() {
    if [ -f '/etc/wpa_supplicant/wpa_supplicant-wlan0.conf' ]; then
        cat '/etc/wpa_supplicant/wpa_supplicant-wlan0.conf'
    else
        echo "${red}Cannot find /etc/wpa_supplicant/wpa_supplicant-wlan0.conf. Please configure it first! ${normal}"
    fi
}

function _deletewificonfig() {
    if [ -f '/etc/wpa_supplicant/wpa_supplicant-wlan0.conf' ]; then
        sudo rm '/etc/wpa_supplicant/wpa_supplicant-wlan0.conf'
        echo "${green}Successfully deleted /etc/wpa_supplicant/wpa_supplicant-wlan0.conf${normal}"
    else
        echo "${red}Cannot find /etc/wpa_supplicant/wpa_supplicant-wlan0.conf to delete!${normal}"
    fi 
}

function _backupwificonfig() {
    _backupfile $WPA_SUPPLICANT_CONFIG_PATH $WPA_SUPPLICANT_CONFIG_BACKUP_PATH
}

function _restorelastusedwificonfig() {
    _restorefile $WPA_SUPPLICANT_CONFIG_BACKUP_PATH $WPA_SUPPLICANT_CONFIG_PATH
}

function _restoredefaultwificonfig() {
    _restorefile $WPA_SUPPLICANT_DEFAULT_CONFIG_PATH $WPA_SUPPLICANT_CONFIG_PATH
}

function _backupfile() {
    if [ -f "$1" ]; then
        sudo cp "$1" "$2"
        echo "${green}Successfully backed up to $2 ${normal}"
    else
        echo "${red}Cannot find $1 ${normal}"
    fi    
}

function _restorefile() {
    if [ -f "$1" ]; then
        sudo cp "$1" "$2"
        echo "${green}Successfully restored from $1 ${normal}"
    else
        echo "${red}Cannot find $1 ${normal}"
    fi    
}

function _list_net_interface() {
    ip a
    _pause
}

function _pause() {
    echo "<Press Enter to continue...>"; read
}

function _askinput() {
    while [[ $action = "" ]]; do
        echo $sep2
        echo "Configure Wifi MENU"
        echo -n ""
        echo -e "1) Configure Wifi"
        echo -e "2) Show wifi config"
        echo -e "3) Delete wifi config"
        echo -e "4) Backup wifi config"
        echo -e "5) Restore last used wifi config"
        echo -e "6) Restore system default wifi config"
        echo -e "7) Enable autostart service"
        echo -e "8) Disable autostart service"
        echo -e "9) List all network interfaces"
        echo -e "99) Exit"
        echo "Enter an action: " ; read response
        case $response in
            01 | 1 ) _configure_wifi ;;
            02 | 2 ) _showwificonfig ;;
            03 | 3 ) _deletewificonfig ;;
            04 | 4 ) _backupwificonfig ;;
            05 | 5 ) _restorelastusedwificonfig ;;
            06 | 6 ) _restoredefaultwificonfig ;;
            07 | 7 ) _enableservicefile ;;
            08 | 8 ) _disableservicefile ;;
            09 | 9 ) _list_net_interface ;;
            99 ) exit ;;
            # "" | * ) action=auto ;;
        esac
    done

    # if [[ $action == config_wifi ]]; then
        # echo "${bold}Configuring wifi...${normal}"
        # _configure_wifi
    # elif [[ $bdscan == list_netif ]]; then
        # echo "${bold}Listing all network interfaces...${normal}"
    # fi
    
}




_askinput
