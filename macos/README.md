You can run rtl_tcp on a mac, and it's available in homebrew:

    brew install librtlsdr moreutils

To get the program to run as a daemon, I recommend setting up a launch daemon

```bash
sudo cp com.rtl-sdr.rtl_tcp.plist /Library/LaunchDaemons/
sudo cp launchctl load /Library/LaunchDaemons/com.rtl-sdr.rtl_tcp.plist 
```

Note this works for Apple Silicon. Intel-based macs will need to update the homebrew 
executable paths in the plist file.