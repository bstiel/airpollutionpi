Air Pollution Pi
----------------

The _Air Pollution Pi_ is a Raspberry Pi air pollution monitoring station. 

It measures:

* Particulate Matter (PM) pollution: PM10 (10 micrometers) and PM2.5 (2.5 micrometers and smaller)
* Nitrogen Dioxide (NO2) (work in progress)
* Temperature
* Humidity
* Barometric Pressure

The _Air Pollition Pi_ takes a reading every 60 seconds. The exact time and location for each reading is recorded.

When  not connected to a Wifi, all readings are written to the Raspberry Pi's SD card.

When connected to a Wifi, any readings on the Raspberry Pi's SD card are sent to the [Air Pollution Pi app](https://github.com/bstiel/airpollutionpi-app).

The Air Pollution Pi app is a self-hosted web application for storage and visualisation of the air pollution data collected by the _Air Pollution Pi_.

The _Air Pollution Pi_ is designed so it can be easily carried around in backpack's or bicycle's bottle holder. It can also be used as a stationary device.


![Air Pollution Pi in a bottle](https://github.com/bstiel/airpollutionpi/raw/master/image01.jpg "Air Pollution Pi in a bottle")


Hardware
------

*this section is still work in progress!*

### Bill of materials


* [Raspberry Pi Zero W](https://shop.pimoroni.com/products/raspberry-pi-zero-w)
* [SDS011 Particulate Matter PM2.5 and PM10 sensor](https://www.ebay.co.uk/itm/292796389252)
* [BME280 Temperature, Humidity and Pressure sensor](https://shop.pimoroni.com/products/adafruit-bme280-i2c-or-spi-temperature-humidity-pressure-sensor)
* [GPS USB Dongle](https://www.ebay.co.uk/itm/GPS-USB-Dongle-Receiver-Windows-10-8-7-Vista-XP-CE-Linux-Google-Earth-Sat-Nav/113247927027)



Software
------

### Flash SD card

For the following steps you need your computer and your SD card mounted.

1. Download [Raspbian Stretch Lite](https://www.raspberrypi.org/downloads/raspbian/) and flash it onto your micro SD card.

2. Create an empty file named `ssh` in the root directory of your SD card.

3. Create an file named `wpa_supplicant.conf` in the root directory of your SD card and the following content:

```
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1
country=GB

network={
        ssid="ssid1"
        psk="password1"
        id_str="a human readable unique name for this wifi"
}

network={
        ssid="ssid2"
        psk="password2"
        id_str="another human readable unique name for this wifi"
}
...
```

Replace `ssid1`, `password` and `a human readable unique name for this wifi` with your Wifi credentials (and a human-readable unique name). You must define one network, you can define more networks.