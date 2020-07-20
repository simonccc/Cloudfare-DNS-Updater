#!/usr/bin/env python3
import json, os, sys
from os.path import isfile
from urllib.request import Request, urlopen

# ?
os.chdir(os.path.dirname(sys.argv[0]))

# Load config
#config = configparser.ConfigParser()
#config.read('config.ini')

DDNS_URL = None
API_URL = None
AUTH_EMAIL = None
AUTH_KEY = None
ZONE = None
ZONE_R = None

try:
  DDNS_URL=os.environ['DDNS_URL']
except:
  DDNS_URL='http://ipv4.icanhazip.com'

try:
  API_URL=os.environ['AUTH_URL']
except:
  DDNS_URL='https://api.cloudflare.com/client/v4/zones'

try:
  AUTH_EMAIL=os.environ['AUTH_EMAIL']
  AUTH_KEY=os.environ['AUTH_KEY']
except:
  print('ERROR: NO EMAIL OR KEY SET')
  sys.exit(1)

try:
  ZONE=os.environ['ZONE']
  ZONE_R=os.environ['ZONE']
except:
  print('ERROR: NO ZONE OR RECORD SET')
  sys.exit(1)


# Get current IP
current_ip_rq = Request(DDNS_URL)
current_ip_rs = urlopen(current_ip_rq).read().decode('utf-8')
current_ip = current_ip_rs.strip()
print('Current IP: %s.' % current_ip)

# Get previous IP
previous_ip = None
try:
    with open('/tmp/ip.txt', 'r') as ip_file:
        previous_ip = ip_file.read()
        print('Previous IP: %s.' % previous_ip)
except Exception as e:
    print(str(e))

# Check if IPs match
if current_ip == previous_ip:
    print('IP has not changed.')
    exit(0)

cf_headers = {
    'X-Auth-Email': AUTH_EMAIL,
    'X-Auth-Key': AUTH_KEY,
    'Content-Type': 'application/json'
}

zone_id = None
record_id = None

# Check if Cloudfare Ids saved
if isfile('/tmp/cloudfare_ids.json'):
    with open('/tmp/cloudfare_ids.json', r) as cloudfare_ids_file:
        cloudfare_ids = json.loads(cloudfare_ids_file.read())
        zone_id = cloudfare_ids['zone_id']
        record_id = cloudfare_ids['record_id']
        print('Cloudfare Ids loaded from file (zone_id=%s,record_id=%s).' % (
            zone_id, record_id))

# Get zone & record Ids if they don't exist
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
            detailurl = '%s/%s/dns_records?name=%s' % ( API_URL, ZONE_R ) 
            detailrq = Request(detailurl, None, cf_headers)
            detailrs = json.loads(urlopen(detailrq).read().decode('utf-8'))
            record_id = detailrs['result'][0]['id']
            try:
                with open('/tmp/cloudfare_ids.json', 'w') as cloudfare_ids_file:
                    cloudfare_ids_file.write(json.dumps({
                        'zone_id': zone_id,
                        'record_id': record_id
                    }))
                print('Saved Cloudfare Ids.')
            except Exception as e:
                print(str(e))
        except Exception as e:
            print('Error getting record id: ' + str(e))

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
            with open('/tmp/ip.txt', 'w') as ip_file:
                ip_file.write(current_ip)
                print('Saved current IP.')
        except Exception as e:
            print(str(e))
    except Exception as e:
        print('Error updating DNS record: ' + str(e))
