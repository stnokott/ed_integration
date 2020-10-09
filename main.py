"""Main file doing all the heavy lifting."""
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
import sqlite3

from db import Database

cwd = os.path.dirname(__file__)

INARA_APP_NAME = "HAIntegration"
CMDR_NAME = "Peek-A-Chu"
URL_SYSTEM = "https://www.edsm.net/api-v1/system"
URL_POSITION = "https://www.edsm.net/api-logs-v1/get-position"
URL_CREDITS = "https://www.edsm.net/api-commander-v1/get-credits"
URL_INARA = "https://inara.cz/inapi/v1/"
URL_EDDB_POP_SYSTEMS_JSON = "https://eddb.io/archive/v6/systems_populated.json"
POP_SYSTEMS_JSON_FILEPATH = os.path.join(cwd, "populated_systems.json")
INI_FILEPATH = os.path.join(cwd, "app.ini")

locale.setlocale(locale.LC_ALL, "")

event_codes_edsm = {
    201: "Commander name not found",
    203: "Invalid API key or commander name",
    208: "No credit-data available",
}


# TODO: error code resolving


class Configuration:
    """
    Contains all configuration, user- and integration-generated.
    """

    __edsm_api_key: str = None
    __inara_api_key: str = None
    __pop_systems_refresh_interval: int = 24
    __pop_systems_last_download: datetime.datetime = None

    def get_edsm_api_key(self):
        """
        Getter for the EDSM API key.
        :return: EDSM API key.
        """
        return self.__edsm_api_key

    def set_edsm_api_key(self, inara_api_key: str):
        self.__edsm_api_key = inara_api_key

    def get_inara_api_key(self):
        """
        Getter for the Inara API key.
        :return: Inara API key.
        """
        return self.__inara_api_key

    def set_inara_api_key(self, inara_api_key: str):
        self.__inara_api_key = inara_api_key

    def get_pop_systems_refresh_interval(self):
        """
        Getter for the interval at which the local database should be refreshed from data online in days,
        i.e. the number of days needed to elapse since last refresh to trigger a refresh.
        :return: Database refresh interval
        :rtype: int
        """
        return self.__pop_systems_refresh_interval

    def set_pop_systems_refresh_interval(self, interval: int):
        self.__pop_systems_refresh_interval = interval
        self.__config[self.__section_user][self.__key_pop_systems_interval] = str(
            interval
        )

    def get_pop_systems_last_download(self):
        """
        Getter for the time of the last system database refresh. Needed to check if a refresh is needed.
        :return: datetime instance
        :rtype: datetime.datetime
        """
        return self.__pop_systems_last_download

    def set_pop_systems_last_download(self, last_download: datetime.datetime):
        self.__pop_systems_last_download = last_download
        self.__config[self.__section_script][self.__key_pop_systems_last_download] = (
            last_download.isoformat() if last_download is not None else "never"
        )

    edsm_api_key = property(get_edsm_api_key, set_edsm_api_key)
    inara_api_key = property(get_inara_api_key, set_inara_api_key)
    pop_systems_refresh_interval = property(
        get_pop_systems_refresh_interval, set_pop_systems_refresh_interval
    )
    pop_systems_last_download = property(
        get_pop_systems_last_download, set_pop_systems_last_download
    )

    __config: configparser.ConfigParser
    __section_user = "CONFIG"
    __key_edsm_api_key = "edsmapikey"
    __key_inara_api_key = "inaraapikey"
    __key_pop_systems_interval = "PopSystemsRefreshInterval"
    __section_script = "SCRIPT"
    __key_pop_systems_last_download = "LastDownloadISO8601"

    def __init__(self):
        ini_modified = False

        c = configparser.ConfigParser()
        if not os.path.isfile(INI_FILEPATH):
            open(INI_FILEPATH, "a").close()
            print("INI file absent, file created.")

        try:
            c.read(INI_FILEPATH)
        except configparser.MissingSectionHeaderError:
            open(INI_FILEPATH, "w").close()
            print("INI file corrupted, contents reset.")

        # USER #
        # Create user section if needed.
        if self.__section_user not in c:
            c[self.__section_user] = {}
            ini_modified = True
            print("Created [%s] section." % self.__section_user)
        config_user = c[self.__section_user]

        # Create or fix <edsm_api_key> if needed
        if self.__key_edsm_api_key not in config_user:
            config_user[self.__key_edsm_api_key] = ""
            ini_modified = True
            print("Set default value for <%s>" % self.__key_edsm_api_key)
        value_edsm_api_key = config_user[self.__key_edsm_api_key]

        # Create or fix <inara_api_key> if needed
        if self.__key_inara_api_key not in config_user:
            config_user[self.__key_inara_api_key] = ""
            ini_modified = True
            print("Set default value for <%s>" % self.__key_inara_api_key)
        value_inara_api_key = config_user[self.__key_inara_api_key]

        # Create or fix <pop_systems_interval> if needed.
        if (
            self.__key_pop_systems_interval not in config_user
            or not config_user[self.__key_pop_systems_interval].isnumeric()
        ):
            config_user[self.__key_pop_systems_interval] = "24"
            ini_modified = True
            print("Set default value for <%s>" % self.__key_pop_systems_interval)
        value_pop_systems_interval = int(config_user[self.__key_pop_systems_interval])

        # SCRIPT #
        # Create script section if needed.
        if self.__section_script not in c:
            c[self.__section_script] = {}
            ini_modified = True
            print("Created [%s] section." % self.__section_script)
        config_script = c[self.__section_script]
        # Create <pop_systems_last_download> if needed.
        if self.__key_pop_systems_last_download not in config_script:
            config_script[self.__key_pop_systems_last_download] = "never"
            ini_modified = True
            print("Set default value for <%s>" % self.__key_pop_systems_last_download)
        try:
            value_pop_systems_last_download = datetime.datetime.fromisoformat(
                config_script[self.__key_pop_systems_last_download]
            )
        except ValueError:
            # Fix <pop_systems_last_download> if needed.
            if config_script[self.__key_pop_systems_last_download] != "never":
                print(
                    "Set default value for <%s>" % self.__key_pop_systems_last_download
                )
            else:
                print(
                    "Invalid value for <%s>, setting to default value."
                    % self.__key_pop_systems_last_download
                )
            config_script[self.__key_pop_systems_last_download] = "never"
            value_pop_systems_last_download = None
            ini_modified = True

        self.__config = c

        if ini_modified:
            self.save()

        # set member values
        self.__inara_api_key = value_inara_api_key
        self.__edsm_api_key = value_edsm_api_key
        self.__pop_systems_refresh_interval = value_pop_systems_interval
        self.__pop_systems_last_download = value_pop_systems_last_download

    def save(self):
        """
        Saves this configuration instance to the corresponding file.
        """
        with open(INI_FILEPATH, "w") as config_file:
            self.__config.write(config_file)
            print("INI file changes saved.")


config = Configuration()
db = Database()


def get_last_known_position_sys():
    """
    Gets an instance of System representing the last known location of the corresponding player from EDSM.
    :return: System instance of last known location
    :rtype: System
    """
    api_key = config.edsm_api_key if config.edsm_api_key != "" else None
    params = {"commanderName": CMDR_NAME, "apiKey": api_key}
    r = requests.get(URL_POSITION, params)
    data = r.json()
    try:
        msgnum = data["msgnum"]
        if msgnum != 100:
            if msgnum in event_codes_edsm:
                return event_codes_edsm[msgnum]
            return "Error: %s" % data["msg"]
        system_name = data["system"]
        return db.get_system_by_name(system_name)
    except (KeyError, TypeError):
        return None


def get_balance():  # TODO: make graph
    """
    Gets current player balance from EDSM.
    :return: Player balance
    :rtype: int
    """
    if config.edsm_api_key is None or config.edsm_api_key == "":
        # TODO: error handling with HASS
        return None
    params = {"commanderName": CMDR_NAME, "apiKey": config.edsm_api_key}
    r = requests.get(URL_CREDITS, params)
    data = r.json()
    try:
        msgnum = data["msgnum"]
        if msgnum != 100:
            if msgnum in event_codes_edsm:
                return event_codes_edsm[msgnum]
            return "Error: %s" % data["msg"]
        credits_ = data["credits"][0]
        balance = credits_["balance"]
        loan = credits_["loan"]
        total = balance - loan
        return "%s Cr" % f"{total:n}"
    except (KeyError, TypeError):
        return None


def is_systems_json_expired():
    """
    Check in accordance to user settings and last refresh if the systems database needs to be refreshed from EDDB.
    :return: Boolean if data is expired
    :rtype: bool
    """
    last_download_time = config.pop_systems_last_download
    if last_download_time is None or not os.path.isfile(POP_SYSTEMS_JSON_FILEPATH):
        return True
    now_time = datetime.datetime.now()
    time_delta = now_time - last_download_time
    return not (
        int(time_delta.total_seconds() / 60 / 60) < config.pop_systems_refresh_interval
    )


def refresh_system_data(reset: bool = False):
    """
    Redownloads system data and refreshes database if needed.
    :param reset: force refresh, ignoring user refresh interval settings
    """
    # check if refresh needed
    if not reset and not is_systems_json_expired():
        print("Skipping refresh of non-expired systems JSON.")
        return
    print("System data expired, redownload needed.")

    params = {"Accept-Encoding": "gzip, deflate, sdch"}
    data = urllib.parse.urlencode(params)
    data = data.encode("ascii")
    print("Getting input stream for %s..." % URL_EDDB_POP_SYSTEMS_JSON, end="")
    with urllib.request.urlopen(URL_EDDB_POP_SYSTEMS_JSON, data) as response, open(
        POP_SYSTEMS_JSON_FILEPATH, "wb"
    ) as out_file:
        print(" Done.")
        print("Writing to %s..." % POP_SYSTEMS_JSON_FILEPATH, end="")
        shutil.copyfileobj(response, out_file)
        print(" Done.")

    print("Updating config for last_download...")
    config.pop_systems_last_download = datetime.datetime.now()
    config.save()

    if reset:
        db.reset()

    # Push changes to database
    try:
        with open(POP_SYSTEMS_JSON_FILEPATH, "r") as systems_json:
            systems = ijson.items(systems_json, "item")
            systems_list = []
            for s in systems:
                systems_list.append(
                    (
                        s["id"],
                        s["edsm_id"],
                        s["name"],
                        float(s["x"]),
                        float(s["y"]),
                        float(s["z"]),
                        s["population"],
                        s["is_populated"],
                        s["government_id"],
                        s["government"],
                        s["allegiance_id"],
                        s["allegiance"],
                        s["security_id"],
                        s["security"],
                        s["primary_economy_id"],
                        s["primary_economy"],
                        s["power"],
                        s["power_state"],
                        s["power_state"],
                        s["needs_permit"],
                        s["updated_at"],
                        s["controlling_minor_faction_id"],
                        s["controlling_minor_faction"],
                        s["reserve_type_id"],
                        s["reserve_type"],
                    )
                )
            db.add_systems(systems_list)
    except sqlite3.Error:
        print("Error while updating systems table.")
        refresh_system_data(True)


def get_cmdr_power_str():
    """
    Gets powerplay faction of player, if known, as string.
    :return: Powerplay faction string, if any
    :rtype: str
    """
    payload = {
        "header": {
            "appName": INARA_APP_NAME,
            "appVersion": "0.0.1",
            "isDeveloped": False,
            "APIkey": config.inara_api_key,
            "commanderName": CMDR_NAME,
        },
        "events": [
            {
                "eventName": "getCommanderProfile",
                "eventTimestamp": datetime.datetime.now().isoformat(),
                "eventData": {"searchName": CMDR_NAME},
            }
        ],
    }
    r = requests.post(URL_INARA, data=json.dumps(payload))
    try:
        header = r.json()["header"]
        if not header["eventStatus"] == 200:
            return None
        event_data = r.json()["events"][0]["eventData"]
        power_name = event_data["preferredPowerName"]
        return power_name if power_name and power_name != "" else None
    except (KeyError, TypeError):
        return None


def get_closest_allied_system():
    """
    Get closest system to the player that is controlled by the player's powerplay faction.
    :return: closest allied system
    :rtype: System
    """
    power = get_cmdr_power_str()
    if power is None or power == "":
        return None
    return db.get_closest_allied_system(
        get_last_known_position_sys().sid, get_cmdr_power_str()
    )


if __name__ == "__main__":
    refresh_system_data()
    system = get_closest_allied_system()
    if system is not None:
        print(system.name)
    else:
        print("n/a")
