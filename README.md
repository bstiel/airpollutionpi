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



Prepare SD card
------

For the following steps you need your computer and your SD card mounted.

1. Download [Raspbian Stretch Lite](https://www.raspberrypi.org/downloads/raspbian/) and flash it onto your micro SD card.

2. Create an empty file named `ssh` in the root directory of your SD card.

3. Create a file named `wpa_supplicant.conf` in the root directory of your SD card. Use this as your file's template:

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

Connect to Raspberry Pi via ssh
------

1. Insert SD card into Raspberry Pi

2. Start Raspberry Pi

3. Find your Raspberry Pi's IP address. Go to the admin website to your Wifi router and go through the list of connected devices. You should see a device named `raspberrypi` and it should display its IP address. Connect from your computer's command line (Mac or Linux): `ssh pi@<raspberry pi IP address>` (password `raspberry`).


Configure Raspberry Pi
------

For the following steps you need to *connected* to your Raspberry Pi via ssh (see above).


1. Run `sudo raspi-config`. This will take you to a menu. With the arrow keys select `5 Interfacing Options`. Then `P5 I2C Enable/Disable automatic loading of I2C kernel module`. Select `Yes` when asked `Would you like the ARM I2C interface to be enabled?` and confirm by pressing enter. When you see `The ARM I2C interface is enabled` screen, confirm by pressing enter. Exit the menu via `Finish` (you get there with the tab key) or the Escape key.

2. Run `sudo apt-get install git python-pip3 -y` 

3. Run `git clone https://github.com/bstiel/airpollutionpi.git` 

4. Run `nano config.yaml`. Copy & paste the content from the `config.yaml` template into the editor. Under server, set the correct values for url, user and password.  When done, exit the nano editor via `Ctrl+X`. Answer `Save modified buffer?"` with `Y` and confirm `File Name to Write: config.yaml` with `Enter`.

5. Test everything is working: `cd airpollutionpi`

6. Test you can collect data from all sensors (cont'd): `python3 snapshot.py` - if everything is ok, you should see a bunch of messages (and no error messages) and the last message should look similiar-ish to:

```
2019-03-06 21:46:02,643 - INFO - __main__ [222] - Write data to file: ['healthcheck,source=pi-in-a-bottle-1,input=internal cpu_temperature=37.932 1551908759869443584', 'weather,source=pi-in-a-bottle-1,input=bme280 humidity=64.8 1551908759869443584', 'weather,source=pi-in-a-bottle-1,input=bme280 temperature=19.22 1551908759869443584', 'weather,source=pi-in-a-bottle-1,input=bme280 pressure=980.47 1551908759869443584', 'pollution,source=pi-in-a-bottle-1,input=sds011 pm2.5=0.4 1551908759869443584', 'pollution,source=pi-in-a-bottle-1,input=sds011 pm10=0.6 1551908759869443584'] => /home/pi/data/1551908759869443584.tmp
2019-03-06 21:46:02,660 - INFO - __main__ [226] - Rename file: /home/pi/data/1551908759869443584.tmp => /home/pi/data/1551908759869443584
```

Also, this should have created a file. Type `ls ../data -l` to confirm. This should give you something like this:

```
total 4
-rw-r--r-- 1 pi pi 489 Mar  6 21:47 1551908826376910848
```

It should list one file and you should see a date and time that is close to now.

7. Test you can broadcast the data to the server: `python3 broadcast.py`. This should respond with something like this:

```
2019-03-06 21:49:44,974 - INFO - __main__ [49] - Collect files in path /home/pi/data
2019-03-06 21:49:44,979 - INFO - __main__ [52] - Found 1 file(s)
2019-03-06 21:49:44,984 - INFO - __main__ [57] - Process file /home/pi/data/1551908945907030016 [2019-03-06T21:49:08.529623]
2019-03-06 21:49:44,989 - INFO - __main__ [61] - POST http://influxdb.datalake.ninja/write?db=timeseries: healthcheck,source=pi-in-a-bottle-1,input=internal cpu_temperature=39.008 1551908945907030016
weather,source=pi-in-a-bottle-1,input=bme280 humidity=64.75 1551908945907030016
weather,source=pi-in-a-bottle-1,input=bme280 temperature=19.23 1551908945907030016
weather,source=pi-in-a-bottle-1,input=bme280 pressure=980.37 1551908945907030016
pollution,source=pi-in-a-bottle-1,input=sds011 pm2.5=0.4 1551908945907030016
pollution,source=pi-in-a-bottle-1,input=sds011 pm10=0.8 1551908945907030016
2019-03-06 21:49:45,046 - DEBUG - urllib3.connectionpool [205] - Starting new HTTP connection (1): influxdb.datalake.ninja:80
2019-03-06 21:49:45,096 - DEBUG - urllib3.connectionpool [393] - http://influxdb.datalake.ninja:80 "POST /write?db=timeseries HTTP/1.1" 204 0
2019-03-06 21:49:45,113 - INFO - __main__ [63] - Response: 204
2019-03-06 21:49:45,119 - INFO - __main__ [73] - Delete file /home/pi/data/1551908945907030016
```

The second line from the bottom should really say `Response: 204`. If there is any other response code which is not 204, something is not right and needs to be fixed before moving on to the next step.

8. Run `crontab -e`. The first time round, it'll ask you:

```
Select an editor.  To change later, run 'select-editor'.
  1. /bin/ed
  2. /bin/nano        <---- easiest
  3. /usr/bin/vim.tiny
```

Select `2` and add these two lines at the bottom:

```
* * * * * python3 /home/pi/airpollutionpi/snapshot.py
* * * * * python3 /home/pi/airpollutionpi/broadcast.py
```

Exit via `Ctrl+X`, `Y` and `Enter`.

Congrats, you made it! Remember to charge your Raspberry Pi whenever you can.