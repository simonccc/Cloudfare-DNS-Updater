#!/usr/bin/env python3
import configparser
import logging
import json
import os
import sys
from os.path import isfile
from urllib.request import Request, urlopen

os.chdir(os.path.dirname(sys.argv[0]))

# Load config
config = configparser.ConfigParser()
config.read('config.ini')

# Setup logging
logging.basicConfig(filename=config['DEFAULT']['log_file'],
                    format='%(asctime)s %(levelname)s - %(message)s', level=logging.INFO)

# Get current IP
current_ip_rq = Request(config['icanhazip']['url'])
current_ip_rs = urlopen(current_ip_rq).read().decode('utf-8')
current_ip = current_ip_rs.strip()
logging.info('Current IP: %s.' % current_ip)

# Get previous IP
previous_ip = None
try:
    with open(config['DEFAULT']['ip_file'], 'r') as ip_file:
        previous_ip = ip_file.read()
        logging.info('Previous IP: %s.' % previous_ip)
except Exception as e:
    logging.error(str(e))

# Check if IPs match
if current_ip == previous_ip:
    logging.info('IP has not changed.')
    exit(0)

cf_headers = {
    'X-Auth-Email': config['Cloudfare']['auth_email'],
    'X-Auth-Key': config['Cloudfare']['auth_key'],
    'Content-Type': 'application/json'
}

zone_id = None
record_id = None

# Check if Cloudfare Ids saved
if isfile(config['DEFAULT']['cloudfare_ids_file']):
    with open(config['DEFAULT']['cloudfare_ids_file'], 'r') as cloudfare_ids_file:
        cloudfare_ids = json.loads(cloudfare_ids_file.read())
        zone_id = cloudfare_ids['zone_id']
        record_id = cloudfare_ids['record_id']
        logging.info('Cloudfare Ids loaded from file (zone_id=%s,record_id=%s).' % (
            zone_id, record_id))

# Get zone & record Ids if they don't exist
if (zone_id is None or record_id is None):
    try:
        zoneurl = '%s?name=%s' % (
            config['Cloudfare']['api_url'], config['Cloudfare']['zone_name'])
        zonerq = Request(zoneurl, None, cf_headers)
        zoners = json.loads(urlopen(zonerq).read().decode('utf-8'))
        zone_id = zoners['result'][0]['id']
    except Exception as e:
        logging.error('Error getting zone id: ' + str(e))

    if zone_id:
        try:
            detailurl = '%s/%s/dns_records?name=%s' % (
                config['Cloudfare']['api_url'], zone_id, config['Cloudfare']['record_name'])
            detailrq = Request(detailurl, None, cf_headers)
            detailrs = json.loads(urlopen(detailrq).read().decode('utf-8'))
            record_id = detailrs['result'][0]['id']
            try:
                with open(config['DEFAULT']['cloudfare_ids_file'], 'w') as cloudfare_ids_file:
                    cloudfare_ids_file.write(json.dumps({
                        'zone_id': zone_id,
                        'record_id': record_id
                    }))
                logging.info('Saved Cloudfare Ids.')
            except Exception as e:
                logging.error(str(e))
        except Exception as e:
            logging.error('Error getting record id: ' + str(e))

# Update IP
if zone_id and record_id:
    updateurl = '%s/%s/dns_records/%s' % (
        config['Cloudfare']['api_url'], zone_id, record_id)
    try:
        content = json.dumps({
            'id': zone_id,
            'type': 'A',
            'name': config['Cloudfare']['record_name'],
            'content': current_ip
        }).encode('utf-8')
        updaterq = Request(updateurl, data=content,
                           method='PUT', headers=cf_headers)
        updaterq.add_header('Content-Length', len(content))
        updaters = urlopen(updaterq)
        logging.info('IP updated to %s.' % current_ip)
        # Set current IP
        try:
            with open(config['DEFAULT']['ip_file'], 'w') as ip_file:
                ip_file.write(current_ip)
                logging.info('Saved current IP.')
        except Exception as e:
            logging.error(str(e))
    except Exception as e:
        logging.error('Error updating DNS record: ' + str(e))
