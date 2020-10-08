import os
import requests
import urllib.request
import urllib.parse
import shutil
import locale
import json
import datetime
import configparser
import ijson
from db import Database
import sqlite3

cwd = os.path.dirname(__file__)

EDSM_API_KEY = '2ead48e5586e056cd566ecce6d692c387f65967b'  # TODO: move to config, check for empty (make None if so)
INARA_API_KEY = 'o2bf28bsd40kwg8sgwks0ok44sgkoso0s444s'
INARA_APP_NAME = 'HAIntegration'
CMDR_NAME = 'Peek-A-Chu'
URL_STATUS = 'https://www.edsm.net/api-status-v1/elite-server'
URL_SYSTEM = 'https://www.edsm.net/api-v1/system'
URL_POSITION = 'https://www.edsm.net/api-logs-v1/get-position'
URL_CREDITS = 'https://www.edsm.net/api-commander-v1/get-credits'
URL_INARA = 'https://inara.cz/inapi/v1/'
URL_EDDB_POP_SYSTEMS_JSON = 'https://eddb.io/archive/v6/systems_populated.json'
POP_SYSTEMS_JSON_FILEPATH = os.path.join(cwd, 'populated_systems.json')
INI_FILEPATH = os.path.join(cwd, 'app.ini')

locale.setlocale(locale.LC_ALL, '')

event_codes_edsm = {
    201: 'Commander name not found',
    203: 'Invalid API key or commander name',
    208: 'No credit-data available'
}


# TODO: error code resolving


class Configuration:
    __pop_systems_refresh_interval: int = 24
    __pop_systems_last_download: datetime.datetime = None

    def get_pop_systems_refresh_interval(self):
        return self.__pop_systems_refresh_interval

    def set_pop_systems_refresh_interval(self, interval: int):
        self.__pop_systems_refresh_interval = interval
        self.__config[self.__section_user][self.__key_pop_systems_interval] = str(interval)

    def get_pop_systems_last_download(self):
        return self.__pop_systems_last_download

    def set_pop_systems_last_download(self, last_download: datetime.datetime):
        self.__pop_systems_last_download = last_download
        self.__config[self.__section_script][self.__key_pop_systems_last_download] = \
            last_download.isoformat() if last_download is not None else 'never'

    pop_systems_refresh_interval = property(get_pop_systems_refresh_interval, set_pop_systems_refresh_interval)
    pop_systems_last_download = property(get_pop_systems_last_download, set_pop_systems_last_download)

    __config: configparser.ConfigParser
    __section_user = 'CONFIG'
    __key_pop_systems_interval = 'PopSystemsRefreshInterval'
    __section_script = 'SCRIPT'
    __key_pop_systems_last_download = 'LastDownloadISO8601'

    def __init__(self):
        ini_modified = False

        c = configparser.ConfigParser()
        if not os.path.isfile(INI_FILEPATH):
            open(INI_FILEPATH, 'a').close()
            print('INI file absent, file created.')

        try:
            c.read(INI_FILEPATH)
        except configparser.MissingSectionHeaderError:
            open(INI_FILEPATH, 'w').close()
            print('INI file corrupted, contents reset.')

        # USER #
        # create user section if needed
        if self.__section_user not in c:
            c[self.__section_user] = {}
            ini_modified = True
            print('Created [%s] section.' % self.__section_user)
        config_user = c[self.__section_user]
        # create or fix <pop_systems_interval> if needed
        if self.__key_pop_systems_interval not in config_user or not config_user[
            self.__key_pop_systems_interval].isnumeric():
            config_user[self.__key_pop_systems_interval] = '24'
            ini_modified = True
            print('Set default value for <%s>' % self.__key_pop_systems_interval)
        value_pop_systems_interval = int(config_user[self.__key_pop_systems_interval])

        # SCRIPT #
        # create script section if needed
        if self.__section_script not in c:
            c[self.__section_script] = {}
            ini_modified = True
            print('Created [%s] section.' % self.__section_script)
        config_script = c[self.__section_script]
        # create <pop_systems_last_download> if needed
        if self.__key_pop_systems_last_download not in config_script:
            config_script[self.__key_pop_systems_last_download] = 'never'
            ini_modified = True
            print('Set default value for <%s>' % self.__key_pop_systems_last_download)
        try:
            value_pop_systems_last_download = datetime.datetime.fromisoformat(
                config_script[self.__key_pop_systems_last_download])
        except ValueError:
            # fix <pop_systems_last_download>
            if config_script[self.__key_pop_systems_last_download] != 'never':
                print('Set default value for <%s>' % self.__key_pop_systems_last_download)
            else:
                print('Invalid value for <%s>, setting to default value.' % self.__key_pop_systems_last_download)
            config_script[self.__key_pop_systems_last_download] = 'never'
            value_pop_systems_last_download = None
            ini_modified = True

        self.__config = c

        if ini_modified:
            self.save()

        # set member values
        self.__pop_systems_refresh_interval = value_pop_systems_interval
        self.__pop_systems_last_download = value_pop_systems_last_download

    def save(self):
        with open(INI_FILEPATH, 'w') as config_file:
            self.__config.write(config_file)
            print('INI file changes saved.')


config = Configuration()
db = Database()


def api_is_online():
    r = requests.get(URL_STATUS)
    return r.json()['status'] == 2


def is_systems_json_expired():
    last_download_time = config.pop_systems_last_download
    if last_download_time is None or not os.path.isfile(POP_SYSTEMS_JSON_FILEPATH):
        return True
    now_time = datetime.datetime.now()
    time_delta = now_time - last_download_time
    return not (int(time_delta.seconds / 60 / 60) < config.pop_systems_refresh_interval)


def refresh_json():
    # check if refresh needed
    if not is_systems_json_expired():
        print('Skipping refresh of non-expired systems JSON.')
        return
    print('System data expired, redownload needed.')

    params = {
        'Accept-Encoding': 'gzip, deflate, sdch'
    }
    data = urllib.parse.urlencode(params)
    data = data.encode('ascii')
    print("Getting input stream for %s..." % URL_EDDB_POP_SYSTEMS_JSON, end="")
    with urllib.request.urlopen(URL_EDDB_POP_SYSTEMS_JSON, data) as response, \
            open(POP_SYSTEMS_JSON_FILEPATH, 'wb') as out_file:
        print(" Done.")
        print("Writing to %s..." % POP_SYSTEMS_JSON_FILEPATH, end="")
        shutil.copyfileobj(response, out_file)
        print(" Done.")

    print('Updating config for last_download...')
    config.pop_systems_last_download = datetime.datetime.now()
    config.save()


def refresh_database(reset: bool = False):
    refresh_json()

    if reset:
        db.reset()

    # Push changes to database
    try:
        with open(POP_SYSTEMS_JSON_FILEPATH, 'r') as systems_json:
            systems = ijson.items(systems_json, 'item')
            systems_list = []
            for s in systems:
                systems_list.append((s['id'], s['edsm_id'], s['name'], float(s['x']), float(s['y']), float(s['z']),
                                     s['population'], s['is_populated'], s['government_id'], s['government'],
                                     s['allegiance_id'], s['allegiance'], s['security_id'], s['security'],
                                     s['primary_economy_id'], s['primary_economy'], s['power'],
                                     s['power_state'], s['power_state'], s['needs_permit'], s['updated_at'],
                                     s['controlling_minor_faction_id'], s['controlling_minor_faction'],
                                     s['reserve_type_id'], s['reserve_type']))
            db.add_systems(systems_list)
    except sqlite3.Error:
        print('Error while updating systems table.')
        refresh_database(True)


def get_cmdr_power():
    payload = {
        'header': {
            'appName': INARA_APP_NAME,
            'appVersion': '0.0.1',
            'isDeveloped': False,
            'APIkey': INARA_API_KEY,
            'commanderName': CMDR_NAME
        },
        'events': [
            {
                'eventName': 'getCommanderProfile',
                'eventTimestamp': datetime.datetime.now().isoformat(),
                'eventData': {
                    'searchName': CMDR_NAME
                }
            }
        ]
    }
    r = requests.post(URL_INARA, data=json.dumps(payload))
    try:
        header = r.json()['header']
        if not header['eventStatus'] == 200:
            return None
        event_data = r.json()['events'][0]['eventData']
        power_name = event_data['preferredPowerName']
        return power_name if power_name and power_name != '' else None
    except (KeyError, TypeError):
        return None


def get_system_allegiance(system_name: str):
    params = {
        'systemName': system_name,
        'showInformation': 1
    }
    r = requests.get(URL_SYSTEM, params)
    try:
        information = r.json()['information']
        if 'allegiance' not in information:
            return 'Independent'
        return information['allegiance']
    except (KeyError, TypeError):
        return None


def get_last_known_position(include_allegiance: bool = False):
    api_key = EDSM_API_KEY if EDSM_API_KEY != '' else None
    params = {
        'commanderName': CMDR_NAME,
        'apiKey': api_key
    }
    r = requests.get(URL_POSITION, params)
    data = r.json()
    try:
        msgnum = data['msgnum']
        if msgnum != 100:
            if msgnum in event_codes_edsm:
                return event_codes_edsm[msgnum]
            return 'Error: %s' % data['msg']
        system_name = data['system']
        allegiance = get_system_allegiance(system_name)
        if allegiance is None or not include_allegiance:
            return system_name
        return '%s (%s)' % (system_name, allegiance)
    except (KeyError, TypeError):
        return 'Unknown Error'


def get_balance():  # TODO: make graph
    if EDSM_API_KEY is None or EDSM_API_KEY == '':
        return 'API key required'
    params = {
        'commanderName': CMDR_NAME,
        'apiKey': EDSM_API_KEY
    }
    r = requests.get(URL_CREDITS, params)
    data = r.json()
    try:
        msgnum = data['msgnum']
        if msgnum != 100:
            if msgnum in event_codes_edsm:
                return event_codes_edsm[msgnum]
            return 'Error: %s' % data['msg']
        credits_ = data['credits'][0]
        balance = credits_['balance']
        loan = credits_['loan']
        total = balance - loan
        return '%s Cr' % f'{total:n}'
    except (KeyError, TypeError):
        return 'Unknown error'


if __name__ == '__main__':
    refresh_database()
    print(db.get_closest_allied_system(1, get_cmdr_power()).name)
