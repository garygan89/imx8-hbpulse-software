#!/bin/bash
# Manual install gstreamer-imx that is packaged to .rpm from Boundary Device nitrogen8m Yocto layer (branch thud)

# convert .rpm to .deb
sudo alien --target=arm64 --scripts gstreamer1.0-plugins-imx-0.13.0+git0+2ec1a7274f-r0.aarch64_mx8m.rpm
sudo alien --target=arm64 --scripts gstreamer1.0-plugins-imx-dbg-0.13.0+git0+2ec1a7274f-r0.aarch64_mx8m.rpm
sudo alien --target=arm64 --scripts gstreamer1.0-plugins-imx-dev-0.13.0+git0+2ec1a7274f-r0.aarch64_mx8m.rpm
sudo alien --target=arm64 --scripts gstreamer1.0-plugins-imx-imxaudio-0.13.0+git0+2ec1a7274f-r0.aarch64_mx8m.rpm
sudo alien --target=arm64 --scripts gstreamer1.0-plugins-imx-imxvpu-0.13.0+git0+2ec1a7274f-r0.aarch64_mx8m.rpm
sudo alien --target=arm64 --scripts gstreamer1.0-plugins-imx-imxvpu-0.13.0+git0+2ec1a7274f-r0.rpm
sudo alien --target=arm64 --scripts gstreamer1.0-plugins-imx-meta-0.13.0+git0+2ec1a7274f-r0.aarch64_mx8m.rpm
sudo alien --target=arm64 --scripts gstreamer1.0-plugins-imx-src-0.13.0+git0+2ec1a7274f-r0.aarch64_mx8m.rpm
sudo alien --target=arm64 --scripts gstreamer1.0-plugins-imx-staticdev-0.13.0+git0+2ec1a7274f-r0.aarch64_mx8m.rpm
sudo alien --target=arm64 --scripts libgstimxcommon2-0.13.0+git0+2ec1a7274f-r0.aarch64_mx8m.rpm
sudo alien --target=arm64 --scripts libimxdmabuffer1-1.0.0+git0+db17cb57d1-r0.aarch64_mx8m.rpm
sudo alien --target=arm64 --scripts libimxdmabuffer-dbg-1.0.0+git0+db17cb57d1-r0.aarch64_mx8m.rpm
sudo alien --target=arm64 --scripts libimxdmabuffer-dev-1.0.0+git0+db17cb57d1-r0.aarch64_mx8m.rpm
sudo alien --target=arm64 --scripts libimxdmabuffer-ptest-1.0.0+git0+db17cb57d1-r0.aarch64_mx8m.rpm
sudo alien --target=arm64 --scripts libimxdmabuffer-src-1.0.0+git0+db17cb57d1-r0.aarch64_mx8m.rpm
sudo alien --target=arm64 --scripts libimxvpuapi2-2-2.0.0+0+8602896764-r0.aarch64_mx8m.rpm
sudo alien --target=arm64 --scripts libimxvpuapi2-dbg-2.0.0+0+8602896764-r0.aarch64_mx8m.rpm
sudo alien --target=arm64 --scripts libimxvpuapi2-dev-2.0.0+0+8602896764-r0.aarch64_mx8m.rpm
sudo alien --target=arm64 --scripts libimxvpuapi2-src-2.0.0+0+8602896764-r0.aarch64_mx8m.rpm

# Install dpkg
sudo dpkg -i gstreamer1.0-plugins-imx_0.13.0+git0+2ec1a7274f-1_arm64.deb
sudo dpkg -i gstreamer1.0-plugins-imx-dbg_0.13.0+git0+2ec1a7274f-1_arm64.deb
sudo dpkg -i gstreamer1.0-plugins-imx-dev_0.13.0+git0+2ec1a7274f-1_arm64.deb
sudo dpkg -i gstreamer1.0-plugins-imx-imxaudio_0.13.0+git0+2ec1a7274f-1_arm64.deb
sudo dpkg -i gstreamer1.0-plugins-imx-imxvpu_0.13.0+git0+2ec1a7274f-1_arm64.deb
sudo dpkg -i gstreamer1.0-plugins-imx-meta_0.13.0+git0+2ec1a7274f-1_arm64.deb
sudo dpkg -i gstreamer1.0-plugins-imx-src_0.13.0+git0+2ec1a7274f-1_arm64.deb
sudo dpkg -i gstreamer1.0-plugins-imx-staticdev_0.13.0+git0+2ec1a7274f-1_arm64.deb
sudo dpkg -i libgstimxcommon2_0.13.0+git0+2ec1a7274f-1_arm64.deb
sudo dpkg -i libimxdmabuffer1_1.0.0+git0+db17cb57d1-1_arm64.deb
sudo dpkg -i libimxdmabuffer-dev_1.0.0+git0+db17cb57d1-1_arm64.deb
sudo dpkg -i libimxdmabuffer-ptest_1.0.0+git0+db17cb57d1-1_arm64.deb
sudo dpkg -i libimxdmabuffer-src_1.0.0+git0+db17cb57d1-1_arm64.deb
sudo dpkg -i libimxvpuapi2-2_2.0.0+0+8602896764-1_arm64.deb
sudo dpkg -i libimxvpuapi2-dbg_2.0.0+0+8602896764-1_arm64.deb
sudo dpkg -i libimxvpuapi2-dev_2.0.0+0+8602896764-1_arm64.deb
sudo dpkg -i libimxvpuapi2-src_2.0.0+0+8602896764-1_arm64.deb

# copy gstreamer from manual install .deb to gstreamer lib installed by apt install
sudo cp /usr/lib/gstreamer-1.0/* /usr/lib/aarch64-linux-gnu/gstreamer-1.0/

# copy libhantro, for some reason it is not packaged as .rpm in Yocto
sudo cp imx-vpu-hantro/usr/include/* /usr/include/
sudo cp imx-vpu-hantro/usr/lib/* /usr/lib/

# check linking
ldconfig
ldd /usr/lib/gstreamer/libgstimxvpu.so
ldd /usr/lib/gstreamer/libgstimxaudio.so
