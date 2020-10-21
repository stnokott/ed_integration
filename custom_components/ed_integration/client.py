"""Main file doing all the heavy lifting."""
import datetime
import json
import locale
import logging
import os
import shutil
import sqlite3
import urllib.parse
import urllib.request

from homeassistant.core import HomeAssistant
import ijson
import requests

from .db import Database, System
from .const import KEY_OUTPUT_LOCATION_STR

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

locale.setlocale(locale.LC_ALL, "")  # auto locale for thousands delimiter

event_codes_edsm = {
    201: "Commander name not found",
    203: "Invalid API key or commander name",
    208: "No credit-data available",
}


# TODO: error code resolving
# TODO: make async

_LOGGER = logging.getLogger(__name__)


class Configuration:
    """
    Contains all configuration, user- and integration-generated.
    """

    __cmdr_name: str = None
    __edsm_api_key: str = None
    __inara_api_key: str = None
    __pop_systems_refresh_interval: int = 24
    __pop_systems_last_download: datetime.datetime = None

    def __init__(
        self, cmdr_name: str, edsm_api_key: str, inara_api_key: str, pop_systems_refresh_interval: int = None
    ):
        # set member values
        self.__cmdr_name = cmdr_name
        self.__inara_api_key = inara_api_key
        self.__edsm_api_key = edsm_api_key
        self.__pop_systems_refresh_interval = pop_systems_refresh_interval or 24
        self.__pop_systems_last_download = datetime.datetime.fromisocalendar(1900, 1, 1)

    def get_cmdr_name(self):
        """
        Getter for in-game CMDR name
        :return CMDR name
        """
        return self.__cmdr_name

    def set_cmdr_name(self, cmdr_name: str):
        self.__cmdr_name = cmdr_name

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

    def get_pop_systems_last_download(self):
        """
        Getter for the time of the last system database refresh. Needed to check if a refresh is needed.
        :return: datetime instance
        :rtype: datetime.datetime
        """
        return self.__pop_systems_last_download

    def set_pop_systems_last_download(self, last_download: datetime.datetime):
        self.__pop_systems_last_download = last_download

    cmdr_name = property(get_cmdr_name, set_cmdr_name)
    edsm_api_key = property(get_edsm_api_key, set_edsm_api_key)
    inara_api_key = property(get_inara_api_key, set_inara_api_key)
    pop_systems_refresh_interval = property(
        get_pop_systems_refresh_interval, set_pop_systems_refresh_interval
    )
    pop_systems_last_download = property(
        get_pop_systems_last_download, set_pop_systems_last_download
    )


class Client:
    """API client"""

    def __init__(self, hass: HomeAssistant, config: Configuration):
        self._hass = hass
        self._config = config
        self._db = Database(_LOGGER)

    async def async_get_data(self):
        """Return data."""
        location_sys = await self.get_last_known_position_sys()
        now = datetime.datetime.now()
        data = {
            "cmdr_name": self._config.cmdr_name,
            "data": {
                "static": f"Providing data for CMDR {self._config.cmdr_name}.",
                "time": f"{now.strftime('%d.%m.%Y, %H:%M:%S')}",
                KEY_OUTPUT_LOCATION_STR: location_sys.name,
                "none": None,
            },
        }
        return data

    async def is_systems_json_expired(self) -> bool:
        """
        Check in accordance to user settings and last refresh if the systems database needs to be refreshed from EDDB.
        :return: Boolean if data is expired
        :rtype: bool
        """
        last_download_time = self._config.pop_systems_last_download
        if last_download_time is None or not os.path.isfile(POP_SYSTEMS_JSON_FILEPATH):
            return True
        now_time = datetime.datetime.now()
        time_delta = now_time - last_download_time
        return not (
            int(time_delta.total_seconds() / 60 / 60)
            < self._config.pop_systems_refresh_interval
        )

    async def refresh_system_data(self, reset: bool = False) -> None:
        """
        Redownloads system data and refreshes database if needed.
        :param reset: force refresh, ignoring user refresh interval settings
        """
        # check if refresh needed
        if not reset and not await self.is_systems_json_expired():
            _LOGGER.debug("Skipping refresh of non-expired systems JSON.")
            return
        _LOGGER.debug("System data expired, redownload needed.")

        params = {"Accept-Encoding": "gzip, deflate, sdch"}
        data = urllib.parse.urlencode(params)
        data = data.encode("ascii")

        def wrapper():
            """Wrapper for sync json retrieval"""
            with urllib.request.urlopen(URL_EDDB_POP_SYSTEMS_JSON, data) as response, open(
                    POP_SYSTEMS_JSON_FILEPATH, "wb"
            ) as out_file:
                _LOGGER.debug("Writing to %s..." % POP_SYSTEMS_JSON_FILEPATH)
                shutil.copyfileobj(response, out_file)
        await self._hass.async_add_executor_job(wrapper)
        _LOGGER.debug("Updating config for last_download...")
        self._config.pop_systems_last_download = datetime.datetime.now()

        if reset:
            self._db.reset()

        # Push changes to database
        try:
            with open(POP_SYSTEMS_JSON_FILEPATH, "r") as systems_json:
                def wrapper():
                    """Wrapper for sync json parsing"""
                    return ijson.items(systems_json, "item")
                systems = await self._hass.async_add_executor_job(wrapper)
                _LOGGER.debug('Systems JSON loaded from filesystem')
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
                await self._db.add_systems(systems_list)
        except sqlite3.Error as e:
            _LOGGER.warning(
                "Error while updating systems table, trying to rebuild database.",
                exc_info=e,
            )
            # TODO: param with retry count, fail after n retries
            await self.refresh_system_data(True)

    async def get_last_known_position_sys(self) -> System:
        """
        Gets an instance of System representing the last known location of the corresponding player from EDSM.
        :return: System instance of last known location
        :rtype: System
        """
        _LOGGER.debug(f"Entering <{self.get_last_known_position_sys.__name__}>")
        api_key = self._config.edsm_api_key if self._config.edsm_api_key != "" else None
        params = {"commanderName": CMDR_NAME, "apiKey": api_key}

        def wrapper():
            """Wrapper for sync position request"""
            return requests.get(URL_POSITION, params)
        r = await self._hass.async_add_executor_job(wrapper)
        data = r.json()
        _LOGGER.debug(f"EDSM response: {data}")
        try:
            msgnum = data["msgnum"]
            if msgnum != 100:
                if msgnum in event_codes_edsm:
                    _LOGGER.warning(f"Unsuccessful EDSM request: {event_codes_edsm[msgnum]}")
                    return System()  # empty
                _LOGGER.warning(f"Unsuccessful EDSM request, undefined response event code: {data['msg']}")
                return System()  # empty
            system_name = data["system"]
            _LOGGER.debug(f"Retrieved current system name: <{system_name}>")
            await self.refresh_system_data()
            return await self._db.get_system_by_name(system_name)
        except (KeyError, TypeError) as e:
            _LOGGER.warning(f"Unknown error occured while parsing response JSON: {e}")
            return System()  # empty

    async def get_balance_str(self) -> str:  # TODO: make graph
        """
        Gets current player balance from EDSM.
        :return: Player balance
        :rtype: int
        """
        if self._config.edsm_api_key is None or self._config.edsm_api_key == "":
            # TODO: error handling with HASS
            return 'No API key provided'
        params = {"commanderName": CMDR_NAME, "apiKey": self._config.edsm_api_key}

        def wrapper():
            """Wrapper for sync balance request"""
            return requests.get(URL_CREDITS, params)
        r = await self._hass.async_add_executor_job(wrapper)
        data = r.json()
        try:
            msgnum = data["msgnum"]
            if msgnum != 100:
                if msgnum in event_codes_edsm:
                    return event_codes_edsm[msgnum]
                return f"Error: {data['msg']}"
            credits_ = data["credits"][0]
            balance = credits_["balance"]
            loan = credits_["loan"]
            total = balance - loan
            return f"{f'{total:n}'} Cr"
        except (KeyError, TypeError) as e:
            return f"Unknown error occured: {e}"

    async def get_cmdr_power_str(self) -> str:
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
                "APIkey": self._config.inara_api_key,
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

        def wrapper():
            """Wrapper for sync cmdr profile request"""
            return requests.post(URL_INARA, data=json.dumps(payload))
        r = await self._hass.async_add_executor_job(wrapper)
        try:
            header = r.json()["header"]
            if header["eventStatus"] != 200:
                _LOGGER.error(f"Inara API error: {header['eventStatusText']}")
                return f"Inara API error: {header['eventStatusText']}"
            event_data = r.json()["events"][0]["eventData"]
            power_name = event_data["preferredPowerName"]
            return power_name if power_name and power_name != "" else None
        except (KeyError, TypeError) as e:
            return f"Unknown error occured: {e}"

    async def get_closest_allied_system(self) -> System:
        """
        Get closest system to the player that is controlled by the player's powerplay faction.
        :return: closest allied system
        :rtype: System
        """
        await self.refresh_system_data()
        power = await self.get_cmdr_power_str()
        last_known_position_sys = await self.get_last_known_position_sys()
        if power is None or power == "":
            return System()  # empty
        return await self._db.get_closest_allied_system(
            last_known_position_sys.sid,
            power,
        )
