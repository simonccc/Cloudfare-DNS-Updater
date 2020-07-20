#!/usr/bin/env python3
import json, os, sys, time
from os.path import isfile
from urllib.request import Request, urlopen

# docker stuff
DDNS_URL = None
API_URL = None
AUTH_EMAIL = None
AUTH_KEY = None
ZONE = None
ZONE_R = None
SLEEP = None

TMP_IP='/tmp/ip.txt'
TMP_ID='/tmp/cloudfare_ids.json'

try:
  SLEEP=os.environ['SLEEP']
except:
  SLEEP=3600

try:
  DDNS_URL=os.environ['DDNS_URL']
except:
  DDNS_URL='http://ipv4.icanhazip.com'

try:
  API_URL=os.environ['AUTH_URL']
except:
  API_URL='https://api.cloudflare.com/client/v4/zones'

try:
  AUTH_EMAIL=os.environ['AUTH_EMAIL']
  AUTH_KEY=os.environ['AUTH_KEY']
except:
  print('ERROR: NO EMAIL OR KEY SET')
  sys.exit(1)

try:
  ZONE=os.environ['ZONE']
  ZONE_R=os.environ['ZONE_R']
except:
  print('ERROR: NO ZONE OR RECORD SET')
  sys.exit(1)

cf_headers = {
    'X-Auth-Email': AUTH_EMAIL,
    'X-Auth-Key': AUTH_KEY,
    'Content-Type': 'application/json'
}

zone_id = None
record_id = None

# Check if Cloudfare Ids saved
if isfile(TMP_ID):
    with open(TMP_ID, 'r') as cloudfare_ids_file:
        cloudfare_ids = json.loads(cloudfare_ids_file.read())
        zone_id = cloudfare_ids['zone_id']
        record_id = cloudfare_ids['record_id']
        print('Cloudfare Ids loaded from file (zone_id=%s,record_id=%s).' % (
            zone_id, record_id))

if (zone_id is None or record_id is None):
    try:
        zoneurl = '%s?name=%s' % ( API_URL, ZONE )
        zonerq = Request(zoneurl, None, cf_headers)
        zoners = json.loads(urlopen(zonerq).read().decode('utf-8'))
        zone_id = zoners['result'][0]['id']
    except Exception as e:
        print('Error getting zone id: ' + str(e))

    if zone_id:
        try:
            detailurl = '%s/%s/dns_records?name=%s' % ( API_URL, zone_id, ZONE_R )
            detailrq = Request(detailurl, None, cf_headers)
            detailrs = json.loads(urlopen(detailrq).read().decode('utf-8'))
            record_id = detailrs['result'][0]['id']
            try:
                with open(TMP_ID, 'w') as cloudfare_ids_file:
                    cloudfare_ids_file.write(json.dumps({
                        'zone_id': zone_id,
                        'record_id': record_id
                    }))
                print('Saved Cloudfare Ids.')
            except Exception as e:
                print(str(e))
        except Exception as e:
            print('Error getting record id: ' + str(e))

while True:
    # Get current IP
    print('Getting IP from:', DDNS_URL)
    current_ip_rq = Request(DDNS_URL)
    current_ip_rs = urlopen(current_ip_rq).read().decode('utf-8')
    current_ip = current_ip_rs.strip()
    print('Current IP: %s.' % current_ip)

    # Get previous IP
    previous_ip = None
    try:
        with open(TMP_IP, 'r') as ip_file:
            previous_ip = ip_file.read()
            print('Previous IP: %s.' % previous_ip)
    except Exception as e:
        print(str(e))

    # Check if IPs match
    if current_ip == previous_ip:
        print('IP has not changed.')
        time.sleep(SLEEP)

    # Update IP
    if zone_id and record_id:
        updateurl = '%s/%s/dns_records/%s' % ( API_URL, zone_id, record_id ) 
        try:
            content = json.dumps({
            'id': zone_id,
            'type': 'A',
            'name': ZONE_R,
            'content': current_ip
            }).encode('utf-8')
            updaterq = Request(updateurl, data=content,
                           method='PUT', headers=cf_headers)
            updaterq.add_header('Content-Length', len(content))
            updaters = urlopen(updaterq)
            print('IP updated to %s.' % current_ip)
            # Set current IP
            try:
                with open(TMP_IP, 'w') as ip_file:
                    ip_file.write(current_ip)
                    print('Saved current IP.')
            except Exception as e:
                print(str(e))
        except Exception as e:
            print('Error updating DNS record: ' + str(e))
