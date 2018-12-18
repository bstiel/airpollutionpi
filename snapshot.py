import os
import math
import time
import logging
import logging.handlers
import json
import pytz
import yaml
import serial
import geohash2
import gps

from uuid import uuid4


# load config
with open(os.path.join(os.path.dirname(__file__), '..', 'config.yaml'), 'r') as f:
    config = yaml.load(f)

# load which sensors we want to use from config
input_sensors = [c.lower() for c in config['data'].get('input', {}).get('sensors', [])]

# configure logger
formatter = logging.Formatter(config['logging']['format'])
log_level = logging.getLevelName(config['logging']['level'])
if not os.path.exists(config['logging']['path']):
    os.makedirs(config['logging']['path'])

file_handler = logging.handlers.RotatingFileHandler(
    os.path.join(config['logging']['path'], 'snapshot.log'),
    maxBytes=10485760,
    backupCount=100,
    encoding='utf-8')
file_handler.setLevel(log_level)
file_handler.setFormatter(formatter)

console_handler = logging.StreamHandler()
console_handler.setLevel(log_level)
console_handler.setFormatter(formatter)

logging.root.setLevel(log_level)
logging.root.addHandler(file_handler)
logging.root.addHandler(console_handler)

logger = logging.getLogger(__name__)

# get output path
path = config['data']['output']

# create path if it does not exist
if not os.path.exists(path):
    os.makedirs(path)

# timeseries id - from yaml, if not provided, defaults to mac
identifier = config['id']

# data
data = []

# get timestamp
timestamp = int(time.time() * 10**9) # influxdb expects epoch in nanoseconds

# raspberry pi internal healthcheck data
if 'healthcheck' in input_sensors:
    cpu_temp = None
    logger.info('Collect raspberry health data')
    try:
        with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
            cpu_temp = float(f.read()) / 1000.
        data.append('healthcheck,source=%s,input=internal cpu_temperature=%s %s' % (identifier, cpu_temp, timestamp))
    except Exception as ex:
        logger.exception(ex)

# GPS
geohash = None
altitude = None
if 'gps' in input_sensors:
    try:
        logger.info('Get GPS fix')
        port = '/dev/ttyACM0'
        ser = serial.Serial(port, baudrate=9600, timeout=0.5)
        continue_ = True
        t = time.time()
        gps_ = {}
        timeout = 2.0
        read = True
        while read and (time.time() - t) < timeout:
            raw = ser.readline().decode('utf-8')
            logger.debug('GPS raw data: %s' % raw)
            nmea = gps.parse(raw)
            if nmea:
                logger.debug('GPS data: %s' % nmea)
                gps_.update(nmea)
        
            # stop if we have both GPRMC and GPGGA
            if 'altitude' in gps_ and 'speed' in gps_:
                read = False
        logger.info('GPS data: %s' % gps_)
        if 'latitude' in gps_ and 'longitude' in gps_:
            gps_['latitude'] = round(gps_['latitude'], 6)
            gps_['longitude'] = round(gps_['longitude'], 6)
            geohash = geohash2.encode(latitude=gps_['latitude'], longitude=gps_['longitude'])
            data.append('position,source=%s,input=gps geohash=%s %s' % (identifier, geohash, timestamp))
            data.append('position,source=%s,input=gps latitude=%s %s' % (identifier, gps_['latitude'], timestamp))
            data.append('position,source=%s,input=gps longitude=%s %s' % (identifier, gps_['longitude'], timestamp))
        if 'speed' in gps_:
            gps_['speed'] = round(gps_['speed'], 0)
            data.append('position,source=%s,input=gps speed=%s %s' % (identifier, gps_['speed'], timestamp))
        if 'altitude' in gps_:
            gps_['altitude'] = round(gps_['altitude'], 0)
            data.append('position,source=%s,input=gps altitude=%s %s' % (identifier, gps_['altitude'], timestamp))
    except Exception as ex:
        logger.exception(ex)


# dht22
if 'dht22' in input_sensors:
    try:
        import Adafruit_DHT as dht
        logger.info('Collect data from DHT22')
        humidity, temperature = dht.read_retry(dht.DHT22, 4)
        if humidity is not None:
            humidity = round(humidity, 2)
            s = 'weather,source=%s,input=dht22' % identifier
            if geohash is not None:
                s += ',geohash=%s' % geohash
            if altitude is not None:
                s += ',altitude=%s' % altitude
            s += ' humidity=%s %s' % (humidity, timestamp)
            data.append(s)
        if temperature is not None:
            temperature = round(temperature, 2)
            s = 'weather,source=%s,input=dht22' % identifier
            if geohash is not None:
                s += ',geohash=%s' % geohash
            if altitude is not None:
                s += ',altitude=%s' % altitude
            s += ' temperature=%s %s' % (temperature, timestamp)
            data.append(s)
    except Exception as ex:
        logger.exception(ex)

# bm280
if 'bme280' in input_sensors:
    try:
        import smbus2, bme280
        port = 1
        address = 0x76
        logger.info('Collect data from BME280')
        bus = smbus2.SMBus(port)
        calibration_params = bme280.load_calibration_params(bus, address)
        bme280_readings = bme280.sample(bus, address, calibration_params)

        if bme280_readings.humidity is not None:
            humidity = round(bme280_readings.humidity, 2)
            s = 'weather,source=%s,input=bme280' % identifier
            if geohash is not None:
                s += ',geohash=%s' % geohash
            if altitude is not None:
                s += ',altitude=%s' % altitude
            s += ' humidity=%s %s' % (humidity, timestamp)
            data.append(s)

        if bme280_readings.temperature is not None:
            temperature = round(bme280_readings.temperature, 2)
            s = 'weather,source=%s,input=bme280' % identifier
            if geohash is not None:
                s += ',geohash=%s' % geohash
            if altitude is not None:
                s += ',altitude=%s' % altitude
            s += ' temperature=%s %s' % (temperature, timestamp)
            data.append(s)

        if bme280_readings.pressure is not None:
            pressure = round(bme280_readings.pressure, 2)
            s = 'weather,source=%s,input=bme280' % identifier
            if geohash is not None:
                s += ',geohash=%s' % geohash
            if altitude is not None:
                s += ',altitude=%s' % altitude
            s += ' pressure=%s %s' % (pressure, timestamp)
            data.append(s)

    except Exception as ex:
        logger.exception(ex)


# sds011
if 'sds011' in input_sensors:
    try:
        from sensors import SDS011
        logger.info('Collect data from SDS011')
        sds011 = SDS011("/dev/ttyUSB0", use_query_mode=True)
        pm25, pm10 = sds011.query()

        if pm25 is not None:
            pm25 = round(pm25, 2)
            s = 'pollution,source=%s,input=sds011' % identifier
            if geohash is not None:
                s += ',geohash=%s' % geohash
            if altitude is not None:
                s += ',altitude=%s' % altitude
            s += ' pm2.5=%s %s' % (pm25, timestamp)
            data.append(s)

        if pm10 is not None:
            pm10 = round(pm10, 2)
            s = 'pollution,source=%s,input=sds011' % identifier
            if geohash is not None:
                s += ',geohash=%s' % geohash
            if altitude is not None:
                s += ',altitude=%s' % altitude
            s += ' pm10=%s %s' % (pm10, timestamp)
            data.append(s)

    except Exception as ex:
        logger.exception(ex)

if data:
    # fname = os.path.join(path, str(uuid4()))
    fname = os.path.join(path, str(timestamp))
    logger.info('Write data to file: %s => %s.tmp' % (data, fname))
    with open(fname + '.tmp', 'w') as f:
        f.write('\n'.join(data))

    logger.info('Rename file: %s.tmp => %s' % (fname, fname))
    os.rename(fname + '.tmp', fname)

else:
    logger.info('No data collected, exit')