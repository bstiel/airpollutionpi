import os
import math
import time
import logging
import logging.handlers
import json
import pytz
import yaml
import serial
import gps

from uuid import uuid4, getnode as get_mac
from datetime import datetime


# load config
with open(os.path.join(os.path.dirname(__file__), '..', 'config.yaml'), 'r') as f:
    config = yaml.load(f)

# load which sensors we want to use from config
input_sensors = [c.lower() for c in config['data']['input']]

if 'dht22' in input_sensors and 'bme280' in input_sensors:
    logger.warning('You are collecting data from DHT22 and BME280. DHT22/BME280 overwrite temperature and humidity.')


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

# get logger
logger = logging.getLogger(__name__)


# get data path
path = config['data']['path']

# create path if it does not exist
if not os.path.exists(path):
    os.makedirs(path)

# timeseries id - from yaml, if not provided, defaults to mac
identifier = config.get('id', ':'.join(("%012x" % get_mac())[i:i+2] for i in range(0, 12, 2)))


# set defaults
cpu_temp = None
pm25 = None
pm10 = None
temperature = None
humidity = None
pressure = None
gps_ = {}

# raspberry pi healthcheck data
if 'healthcheck' in input_sensors:
    logger.info('Collect raspberry health data')
    with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
        cpu_temp = float(f.read()) / 1000.

# GPS
if 'gps' in input_sensors:
    logger.info('Get GPS fix')
    port = '/dev/ttyACM0'
    ser = serial.Serial(port, baudrate=9600, timeout=0.5)
    continue_ = True
    t = time.time()
    data = None
    while not data and (time.time() - t) < 2.0:
        data = gps.parse(ser.readline())
    if data:
        logger.info('GPS data: %s' % data)
    else:
        logger.info('No GPS data avail')


# DHT22
if 'dht22' in input_sensors:
    import Adafruit_DHT as dht
    logger.info('Collect data from DHT22')
    humidity, temperature = dht.read_retry(dht.DHT22, 4)

# bm280
if 'bme280' in input_sensors:
    import smbus2, bme280
    port = 1
    address = 0x76
    logger.info('Collect data from BME280')
    bus = smbus2.SMBus(port)
    calibration_params = bme280.load_calibration_params(bus, address)
    data = bme280.sample(bus, address, calibration_params)
    humidity = data.humidity
    temperature = data.temperature
    pressure = data.pressure

# sds011
if 'sds011' in input_sensors:
    from sensors import SDS011
    try:
        logger.info('Collect data from SDS011')
        sds011 = SDS011("/dev/ttyUSB0", use_query_mode=True)
        pm25, pm10 = sds011.query()
    except Exception as ex:
        logger.warning('Could not read particulate matter data', exc_info=True)


# round humidity and temperature
if humidity is not None:
    humidity = round(humidity, 2)

if temperature is not None:
    temperature = round(temperature, 2)

if pressure is not None:
    pressure = round(pressure, 2)

# make timestamp timezone-aware
timestamp = datetime.utcnow().replace(tzinfo=pytz.UTC)

# create json
reading = {
    'ts': timestamp.isoformat(),
    'id': identifier,
    'gps': gps_,
    'data': {}
}

if cpu_temp is not None:
    reading['data']['_cpu_temperature'] = cpu_temp

if temperature is not None:
    reading['data']['temperature'] = temperature

if humidity is not None:
    reading['data']['humidity'] = humidity

if pressure is not None:
    reading['data']['pressure'] = pressure

if pm25 is not None:
    reading['data']['PM2.5'] = pm25

if pm10 is not None:
    reading['data']['PM10'] = pm10

if reading['data']:
    fname = os.path.join(path, str(uuid4()))
    logger.info('Write data to file: %s => %s.tmp' % (reading, fname))
    with open(fname + '.tmp', 'w') as f:
        json.dump(reading, f)

    logger.info('Rename file: %s.tmp => %s' % (fname, fname))
    os.rename(fname + '.tmp', fname)

else:
    logger.info('No data collected, exit')