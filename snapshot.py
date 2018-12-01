import os
import time
import json
import pytz
import Adafruit_DHT as dht
import yaml

from uuid import uuid4, getnode as get_mac
from datetime import datetime

# load config
with open('config.yaml', 'r') as f:
    config = yaml.load(f)

# get data path
path = config['data']['path']

# create path if it does not exist
if not os.path.exists(path):
    os.makedirs(path)

# custom labels
labels = config.get('labels', {})

# default labels
labels.update({
    'mac': ':'.join(("%012X" % get_mac())[i:i+2] for i in range(0, 12, 2))
})

# collect raspberry pi healthcheck data
with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
    cpu_temp = float(f.read()) / 1000.

# taske the humidity and temp reading
humidity, temperature = dht.read_retry(dht.DHT22, 4)

# round humidity and temperature
humidity = round(humidity, 2)
temperature = round(temperature, 2)

# make timestamp timezone-aware
timestamp = datetime.utcnow().replace(tzinfo=pytz.UTC)

# create json
reading = {
    'ts': timestamp.isoformat(),
    'labels': labels,
    'data': {
        'h': humidity,
        't': temperature,
        '_': {
            't': cpu_temp
        }
    }
}

fname = os.path.join(path, str(uuid4()))
with open(fname + '.tmp', 'w') as f:
    json.dump(reading, f)

os.rename(fname + '.tmp', fname)