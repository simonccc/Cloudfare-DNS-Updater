# Cloudfare DNS Updater

## About
Small python script that updates DNS record on a Cloudfare domain to achieve DDNS.

## Usage

1. Download https://github.com/mscribellito/Cloudfare-DNS-Updater/archive/master.zip
2. Extract and grant execute permissions to `cfdnsupdate.py`
   * `chmod +x cfdnsupdate.py`
3. Open `config.ini` and update following values based on your Cloudfare account:
   * **auth_email** - email address for your account
   * **auth_key** - Global API Key for your account
   * **zone_name** - domain name
   * **record_name** - record name
4. Schedule run with crontab - below will run every 6 hours
   * `0 */6 * * * /usr/bin/python3 /etc/cf/cfdnsupdate.py`
