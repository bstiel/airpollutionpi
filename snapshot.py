import os
import time
import logging
import logging.handlers
import json
import pytz
import Adafruit_DHT as dht
import yaml

from uuid import uuid4, getnode as get_mac
from datetime import datetime
from sensors import SDS011


# load config
with open(os.path.join(os.path.dirname(__file__), '..', 'config.yaml'), 'r') as f:
    config = yaml.load(f)


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

# collect raspberry pi healthcheck data
logger.info('Collect raspberry health data')
with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
    cpu_temp = float(f.read()) / 1000.

# take the humidity and temp reading
logger.info('Collect DHT22 data')
humidity, temperature = dht.read_retry(dht.DHT22, 4)

# take the pm2.5 and pm10 readings
pm25 = None
pm10 = None
try:
    logger.info('Collect particulate matter data')
    sds011 = SDS011("/dev/ttyUSB0", use_query_mode=True)
    pm25, pm10 = sds011.query()
except Exception as ex:
    logger.warning('Could not read particulate matter data', exc_info=True)


# round humidity and temperature
if humidity is not None:
    humidity = round(humidity, 2)

if temperature is not None:
    temperature = round(temperature, 2)

# make timestamp timezone-aware
timestamp = datetime.utcnow().replace(tzinfo=pytz.UTC)

# create json
reading = {
    'ts': timestamp.isoformat(),
    'id': identifier,
    'data': {
        '_cpu_temperature': cpu_temp
    }
}

if temperature is not None:
    reading['data']['temperature'] = temperature


if humidity is not None:
    reading['data']['humidity'] = humidity


if pm25 is not None:
    reading['data']['PM2.5'] = pm25

if pm10 is not None:
    reading['data']['PM10'] = pm10

fname = os.path.join(path, str(uuid4()))
logger.info('Write data to file: %s => %s.tmp' % (reading, fname))
with open(fname + '.tmp', 'w') as f:
    json.dump(reading, f)

logger.info('Rename file: %s.tmp => %s' % (fname, fname))
os.rename(fname + '.tmp', fname)