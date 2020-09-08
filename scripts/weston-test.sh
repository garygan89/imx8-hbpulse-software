#!/bin/bash
# Test weston compositor

function _checkfbdev() {
    echo "Check if /dev/fb0 exist..."

    ls /dev/fb0 > /dev/null
    if [ ! $? -eq 0 ]; then
        echo "Cannot find /dev/fb0"
        exit 1
    else
        echo "OK"
    fi
}

function _launchweston() {
    # Stop X xerver
    sudo service gdm stop; sudo pkill -9 Xorg
    # Environment and directory setup
    unset DISPLAY
    mkdir /tmp/xdg
    chmod 700 /tmp/xdg
     
    # Choose a valid tty
    export WESTON_TTY=1 
     
    # Launch Weston
    # need to use fbdev-backend, otherwise following will have seg fault
    # sudo XDG_RUNTIME_DIR=/tmp/xdg weston --tty="$WESTON_TTY" --idle-time=0 & 
    # Optional: WAYLAND_DEBUG=server
    # Optional: use --use-egldevice to disable gbm swapchains and use EGLStreams at weston output
    sudo XDG_RUNTIME_DIR=/tmp/xdg weston --tty="$WESTON_TTY" --idle-time=0 --backend=fbdev-backend.so &

    # run sample code
    sudo XDG_RUNTIME_DIR=/tmp/xdg weston-terminal
    # should show spinning triangle
    sudo XDG_RUNTIME_DIR=/tmp/xdg weston-simple-egl
    # should show a white clover
    sudo XDG_RUNTIME_DIR=/tmp/xdg weston-flower
}

_checkfbdev

echo "Launching weston desktop compositor, you should see a desktop interface..."
_launchweston




