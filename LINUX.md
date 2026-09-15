# Raspberry Pi

# Update memory parameter

    sudo nano /boot/firmware/cmdline.txt

Then, append (same line, space-separated):

    usbcore.usbfs_memory_mb=1000


# systemd

Add the systemd service unit:

    cp rtl_tcp.service /etc/systemd/system
    sudo systemctl daemon-reload
    sudo systemctl enable --now rtl_tcp


    

