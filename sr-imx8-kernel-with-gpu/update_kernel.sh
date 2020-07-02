#!/bin/bash
# downgrade kernel to support gpu
export RELEASE=4.19.35-imx8-sr+

# Unpack on target system
sudo tar --keep-directory-symlink -C / -xvf kernel-$RELEASE.tar
# make initrd
sudo update-initramfs -c -k $RELEASE
# select new kernel for future boots
sudo flash-kernel --force $RELEASE