import os
import logging
import logging.handlers
import json
import yaml
import requests

from datetime import datetime


# load config
with open(os.path.join(os.path.dirname(__file__), '..', 'config.yaml'), 'r') as f:
    config = yaml.load(f)

# configure logger
formatter = logging.Formatter(config['logging']['format'])
log_level = logging.getLevelName(config['logging']['level'])
if not os.path.exists(config['logging']['path']):
    os.makedirs(config['logging']['path'])

file_handler = logging.handlers.RotatingFileHandler(
    os.path.join(config['logging']['path'], 'broadcast.log'),
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

# get url and token
url = config['server']['url']
token = config['server']['token']

# get all files (exclude .tmp files)
logger.info('Collect files in path %s' % path)
files = [os.path.join(path, f) for f in os.listdir(path) if not f.endswith('.tmp')]

logger.info('Found %s file(s)' % len(files))
for fname in files:
    delete_file = False
    try:
        last_modified = os.path.getmtime(fname)
        logger.info('Process file %s [%s]' % (fname, datetime.fromtimestamp(last_modified).isoformat()))
        with open(fname, 'r') as f:
            data = json.load(f)
        payload = [data]
        logger.info('POST %s: %s' % (url, payload))
        response = requests.post(url, json=payload, headers={'Authorization': token})
        logger.info('Response: %s' % response.status_code)
        if response.ok:
            delete_file = True
    except json.decoder.JSONDecodeError:
        logger.info('File %s contains invalid json' % fname)
        delete_file = True
    except Exception as ex:
        logger.warning('Exception while trying to POST:', exc_info=True)

    if delete_file:
        logger.info('Delete file %s' % fname)
        os.remove(fname)