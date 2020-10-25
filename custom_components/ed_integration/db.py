"""Provides system database related functions"""
import datetime
import logging
from math import pow, sqrt
import os
import sqlite3 as sql
from typing import List, Tuple

cwd = os.path.dirname(__file__)
DB_FILEPATH = os.path.join(cwd, "database.db")
SQL_RESET_DB_FILEPATH = os.path.join(cwd, "sqls", "init.sql")
SQL_GET_DB_TABLES_FILEPATH = os.path.join(cwd, "sqls", "get_tables_in_db.sql")
SQL_UPDATE_SYSTEM_FILEPATH = os.path.join(cwd, "sqls", "update_system.sql")
SQL_GET_LAST_UPDATED_DATE = os.path.join(cwd, "sqls", "get_last_updated_date.sql")
SQL_SET_LAST_UPDATED_DATE = os.path.join(cwd, "sqls", "update_last_updated_date.sql")
DB_TABLES = ["SYSTEMS", "SYSTEMS_META"]


class System:
    """
    Represents a single system as existing in EDDB API JSON.
    """

    def __init__(
            self,
            sid: int = -1,
            edsm_id: int = -1,
            name: str = 'n/a',
            x: float = 0,
            y: float = 0,
            z: float = 0,
            population: int = -1,
            is_populated: bool = True,
            government_id: int = -1,
            government: str = 'n/a',
            allegiance_id: int = -1,
            allegiance: str = 'n/a',
            security_id: int = -1,
            security: str = 'n/a',
            primary_economy_id: int = -1,
            primary_economy: str = 'n/a',
            power: str = 'n/a',
            power_state: str = 'n/a',
            power_state_id: int = -1,
            needs_permit: bool = False,
            updated_at: int = -1,
            controlling_minor_faction_id: int = -1,
            controlling_minor_faction: str = 'n/a',
            reserve_type_id: int = -1,
            reserve_type: str = 'n/a',
    ):
        self.sid = sid
        self.edsm_id = edsm_id
        self.name = name
        self.x = x
        self.y = y
        self.z = z
        self.population = population
        self.is_populated = is_populated
        self.government_id = government_id
        self.government = government
        self.allegiance_id = allegiance_id
        self.allegiance = allegiance
        self.security_id = security_id
        self.security = security
        self.primary_economy_id = primary_economy_id
        self.primary_economy = primary_economy
        self.power = power
        self.power_state = power_state
        self.power_state_id = power_state_id
        self.needs_permit = needs_permit
        self.updated_at = updated_at
        self.controlling_minor_faction_id = controlling_minor_faction_id
        self.controlling_minor_faction = controlling_minor_faction
        self.reserve_type_id = reserve_type_id
        self.reserve_type = reserve_type


class Database:
    """
    Represents a database of populated E:D systems and provides useful functions to retrieve data from it.
    """

    def __init__(self, logger: logging.Logger):
        self.__conn = sql.connect(DB_FILEPATH)
        self._logger = logger
        self._logger.debug("Connected to database.")

        # Register custom functions
        self.__conn.create_function("sqrt", 1, sqrt)
        self.__conn.create_function("pow", 2, pow)
        self._logger.debug("Registered custom functions.")

        with open(SQL_UPDATE_SYSTEM_FILEPATH) as insert_station_sql_file:
            self.__update_station_sql_str = insert_station_sql_file.read()
        with open(SQL_GET_DB_TABLES_FILEPATH) as get_db_tables_sql_file:
            self.__get_db_tables_sql_str = get_db_tables_sql_file.read()
        with open(SQL_RESET_DB_FILEPATH) as reset_db_file:
            self.__reset_db_sql_str = reset_db_file.read()
        with open(SQL_GET_LAST_UPDATED_DATE) as get_last_updated_date_file:
            self.__get_last_updated_date = get_last_updated_date_file.read()
        with open(SQL_SET_LAST_UPDATED_DATE) as set_last_updated_date_file:
            self.__set_last_updated_date = set_last_updated_date_file.read()
        self._logger.debug("Retrieved prefab sql scripts.")

        query = self.__conn.execute(self.__get_db_tables_sql_str)
        table_list = (t[0] for t in query.fetchall())
        if not set(DB_TABLES) <= set(table_list):  # if tables not in db, do reset
            self.reset()

    def reset(self) -> None:
        """
        Drops and recreates all database tables, dropping all data (!).
        """
        self._logger.debug("Resetting database...")
        self.__conn.executescript(self.__reset_db_sql_str)
        self.__conn.commit()

    async def add_system(
            self,
            sid: int,
            edsm_id: int,
            name: str,
            x: float,
            y: float,
            z: float,
            population: int,
            is_populated: bool,
            government_id: int,
            government: str,
            allegiance_id: int,
            allegiance: str,
            security_id: int,
            security: str,
            primary_economy_id: int,
            primary_economy: str,
            power: str,
            power_state: str,
            power_state_id: int,
            needs_permit: bool,
            updated_at: int,
            controlling_minor_faction_id: int,
            controlling_minor_faction: str,
            reserve_type_id: int,
            reserve_type: str,
    ) -> None:
        """
        Add a system from data primarily existing in the EDDB API systems JSON.
        :param sid: EDDB system ID
        :param edsm_id: EDSM system ID
        :param name: system name
        :param x: system x-coordinate
        :param y: system y-coordinate
        :param z: system z-coordinate
        :param population: system population
        :param is_populated: boolean defining if system is populated
        :param government_id: EDDB government ID
        :param government: government string
        :param allegiance_id: EDDB allegiance ID
        :param allegiance: allegiance string
        :param security_id: EDDB security type ID
        :param security: security string
        :param primary_economy_id: EDDB primary economy ID
        :param primary_economy: primary economy string
        :param power: power name
        :param power_state: power state string
        :param power_state_id: EDDB power state ID
        :param needs_permit: boolean if entering this system in E:D requires a permit
        :param updated_at: UNIX timestamp for the last time this system got updated in EDDB
        :param controlling_minor_faction_id: EDDB controlling minor faction ID
        :param controlling_minor_faction: controlling minor faction string
        :param reserve_type_id: EDDB mineral reserve type ID
        :param reserve_type: mineral reservere type string
        """
        self.__conn.execute(
            self.__update_station_sql_str,
            (
                sid,
                edsm_id,
                name,
                x,
                y,
                z,
                population,
                is_populated,
                government_id,
                government,
                allegiance_id,
                allegiance,
                security_id,
                security,
                primary_economy_id,
                primary_economy,
                power,
                power_state,
                power_state_id,
                needs_permit,
                updated_at,
                controlling_minor_faction_id,
                controlling_minor_faction,
                reserve_type_id,
                reserve_type,
            ),
        )
        self.__conn.commit()

    async def add_systems(
            self,
            systems: List[
                Tuple[
                    int,
                    int,
                    str,
                    float,
                    float,
                    float,
                    int,
                    bool,
                    int,
                    str,
                    int,
                    str,
                    int,
                    str,
                    int,
                    str,
                    str,
                    str,
                    int,
                    bool,
                    int,
                    int,
                    str,
                    int,
                    str,
                ]
            ],
    ) -> None:
        """
        Add multiple systems in one database commit.
        :param systems: list of tuple as described in add_system
        """
        self._logger.debug("Adding %i system rows...", len(systems))
        self.__conn.executemany(self.__update_station_sql_str, systems)
        self.__conn.commit()

    async def get_system_by_id(self, sid: int) -> System:
        """
        Gets System instance from database by its ID
        :param sid: seeked system ID
        :return: System instance, if found
        """
        self._logger.debug(f"Entering <{self.get_system_by_id.__name__}>")
        select_sql_str = (
            "SELECT id, edsm_id, name, x, y, z, population, is_populated, government_id, government, "
            "allegiance_id, allegiance, security_id, security, primary_economy_id, primary_economy, "
            "power, power_state, power_state_id, needs_permit, updated_at, controlling_minor_faction_id, "
            "controlling_minor_faction, reserve_type_id, reserve_type "
            "FROM SYSTEMS WHERE id = ?"
        )
        query = self.__conn.execute(select_sql_str, [sid])
        result = query.fetchone()
        if result is None:
            self._logger.debug("No system retrieved from db, returning n/a")
            return System(sid=sid)
        system = System(*result)
        self._logger.debug(f"Retrieved system from db: <{system.name}>")
        return system

    async def get_system_by_name(self, name: str) -> System:
        """
        Gets System instance from database by its name
        :param name: seeked system name
        :return: System instance, if found
        """
        self._logger.debug(f"Entering <{self.get_system_by_name.__name__}>")
        select_sql_str = (
            "SELECT id, edsm_id, name, x, y, z, population, is_populated, government_id, government, "
            "allegiance_id, allegiance, security_id, security, primary_economy_id, primary_economy, "
            "power, power_state, power_state_id, needs_permit, updated_at, controlling_minor_faction_id, "
            "controlling_minor_faction, reserve_type_id, reserve_type "
            "FROM SYSTEMS WHERE name = ?"
        )
        query = self.__conn.execute(select_sql_str, [name])
        result = query.fetchone()
        if result is None:
            self._logger.debug(f"No system retrieved from db, returning unpopulated system: <{name}>")
            return System(name=name, is_populated=False)
        system = System(*result)
        self._logger.debug(f"Retrieved system from db: <{system.name}>")
        return system

    async def get_closest_allied_system(self, ref_sid: int, power: str) -> System:
        """
        Gets closest system in 3D space that is under control by the specified powerplay faction.
        :param ref_sid: EDDB ID of reference system
        :param power: name of reference powerplay faction
        :return: System instance, if found. None if player is not pledged.
        """
        if power is None or power == "":
            # TODO: replace with exception
            return System(name='Not pledged', sid=ref_sid)
        calc_sql_str = (
            "WITH distances AS ("
            "   SELECT b.id as id,"
            "          b.name,    "
            "          sqrt(pow(b.x - a.x, 2) + pow(b.y - a.y, 2) + pow(b.z - a.z, 2)) as distance "
            "   FROM (SELECT x, y, z"
            "         FROM SYSTEMS"
            "        WHERE id = ?) a"
            "   JOIN (SELECT x, y, z, id, name"
            "        FROM SYSTEMS"
            "        WHERE id != ? AND power = ? AND power_state = 'Control') b"
            ")"
            "SELECT id, min(distance) FROM distances"
        )
        query = self.__conn.execute(calc_sql_str, [ref_sid, ref_sid, power])
        result = query.fetchone()
        return await self.get_system_by_id(result[0])

    async def get_last_refreshed_datetime(self) -> datetime.datetime:
        """
        Gets date of last system data update from db
        """
        query = self.__conn.executescript(self.__get_last_updated_date)
        result = query.fetchone()[0]
        self._logger.debug(f"Retrieved last_refreshed: {result}")
        return result

    async def set_last_refreshed_datetime(self, last_refreshed: datetime.datetime) -> None:
        """
        Writes date of last_system_date_update to db
        """
        self.__conn.execute(self.__set_last_updated_date, [last_refreshed])
        self.__conn.commit()
        self._logger.debug('Updated last_updated in db.')

    def __del__(self):
        self.__conn.close()
        self._logger.debug("Connection to database closed.")
