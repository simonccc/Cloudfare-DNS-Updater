# Cloudfare DNS Updater

Dockerised version of the great work from: https://github.com/mscribellito/Cloudfare-DNS-Updater

## Requirements
1. A domain you own that points to Cloudfare's nameservers
2. the target record must already exist; so create it manually first pointing to eg 127.0.0.1

# Docker

'''docker pull simonczuzu/cloudflare-ddns:latest'''

see below for how to configure it

# Example docker-compose file
'''
version: '3'

services:
    cf_ddns:
      image: cf_ddns
      container_name: cf_ddns
      restart: unless-stopped
      hostname: cn_ddns
      environment:
#        - DDNS_URL=http://ipv4.icanhazip.com
#        - API_URL=https://api.cloudflare.com/client/v4/zones
#        - SLEEP=3600
        - AUTH_EMAIL=email@email.email
        - AUTH_KEY=kekekekekekeyy123
        - ZONE=mydnszone.com
        - ZONE_R=home.mydnszone.com
'''
