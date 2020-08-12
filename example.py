import requests
import locale

EDSM_API_KEY = '2ead48e5586e056cd566ecce6d692c387f65967b'  # TODO: move to config, check for empty (make None if so)
CMDR_NAME = 'Peek-A-Chu'
URL_STATUS = 'https://www.edsm.net/api-status-v1/elite-server'
URL_SYSTEM_INFO = 'https://www.edsm.net/api-v1/system'
URL_LAST_LOCATION = 'https://www.edsm.net/api-logs-v1/get-position'
URL_BALANCE = 'https://www.edsm.net/api-commander-v1/get-credits'

locale.setlocale(locale.LC_ALL, '')


def api_is_online():
    r = requests.get(URL_STATUS)
    return r.json()['status'] == 2


def get_system_allegiance(system_name: str):
    params = {
        'systemName': system_name,
        'showInformation': 1
    }
    r = requests.get(URL_SYSTEM_INFO, params)
    try:
        return r.json()['information']['allegiance']
    except (KeyError, TypeError):
        return None


def get_last_known_position(include_allegiance: bool):
    api_key = EDSM_API_KEY if EDSM_API_KEY != '' else None
    params = {
        'commanderName': CMDR_NAME,
        'apiKey': api_key
    }
    r = requests.get(URL_LAST_LOCATION, params)
    data = r.json()
    try:
        if data['msgnum'] != 100:
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
    r = requests.get(URL_BALANCE, params)
    data = r.json()
    try:
        if data['msgnum'] != 100:
            return 'Error: %s' % data['msg']
        credits_ = data['credits'][0]
        balance = credits_['balance']
        loan = credits_['loan']
        total = balance - loan
        return '%s Cr' % f'{total:n}'
    except (KeyError, TypeError):
        return 'Unknown error'


if __name__ == '__main__':
    print(get_balance())
