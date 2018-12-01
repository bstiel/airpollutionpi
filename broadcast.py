import requests
import os
import json
import yaml

# load config
with open('config.yaml', 'r') as f:
    config = yaml.load(f)


# get data path
path = config['data']['path']

# get url and token
url = config['server']['url']
token = config['server']['token']

# get all files (exclude .tmp files)
files = [os.path.join(path, f) for f in os.listdir(path) if not f.endswith('.tmp')]

for fname in files:
    delete_file = False
    try:
        with open(fname, 'r') as f:
            data = json.load(f)
        response = requests.post(url, json=[data], headers={'Authorization': token})
        if response.ok:
            delete_file = True
    except json.decoder.JSONDecodeError:
        delete_file = True
    if delete_file:
        os.remove(fname)