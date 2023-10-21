# gas-water-meter
Uses RTL-SDR and [rtlamr](https://github.com/bemasher/rtlamr) to read radio signals containing
gas and water consumption, then publish to MQTT.

I use this to expose the data to my [Home Assistant](https://www.home-assistant.io) server.

# Prereqs
You need the `rtl_tcp` program running. `rtl_tcp` must have access to the USB radio device that 
decodes the signals from the utility meters.

## macOS

    brew install librtlsdr libusb-1.0

## Linux
Use your package manager, it might be there. IDK.

## build
Download the sources and build them yourself:

```bash
git clone https://gitea.osmocom.org/sdr/rtl-sdr.git
cd rtl-sdr
mkdir build
cd build
cmake ..
make
sudo make install
```

## Startup
One installed, start it on the machine where the radio is connected to the USB bus. To use docker, you will need to bind 
to an interface accessible to docker.  Here, I'm on an internal host not exposed to the internet, so I just bind on all addresses.

```bash
rtl_tcp -a 0.0.0.0
```
     

# Usage
Edit envvars in `docker-compose.yaml`, esp the `RTLTCP_SERVER` parameter, which will be the IP address of the WiFi or 
Ethernet interface of the machine running `rtl_tcp`

    docker compose up --build -d

The container runs with the "restart unless stopped" policy, so it will run as long as you don't stop it and the docker 
daemon is running on your machine.
