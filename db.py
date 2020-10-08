import sqlite3 as sql
import os

from typing import List, Tuple

cwd = os.path.dirname(__file__)
DB_FILEPATH = os.path.join(cwd, 'database.db')
SQL_RESET_DB_FILEPATH = os.path.join(cwd, 'sqls', 'init.sql')
SQL_GET_DB_TABLES_FILEPATH = os.path.join(cwd, 'sqls', 'get_tables_in_db.sql')
SQL_UPDATE_SYSTEM_FILEPATH = os.path.join(cwd, 'sqls', 'update_system.sql')


class System:
    def __init__(self, sid: int, edsm_id: int, name: str, x: float, y: float, z: float, population: int,
                 is_populated: bool, government_id: int, government: str, allegiance_id: int, allegiance: str,
                 security_id: int, security: str, primary_economy_id: int, primary_economy: str, power: str,
                 power_state: str, power_state_id: int, needs_permit: bool, updated_at: int,
                 controlling_minor_faction_id: int, controlling_minor_faction: str,
                 reserve_type_id: int, reserve_type: str):
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
    def __init__(self):
        self.__conn = sql.connect(DB_FILEPATH)
        print('Connected to database.')

        with open(SQL_UPDATE_SYSTEM_FILEPATH) as insert_station_sql_file:
            self.__update_station_sql_str = insert_station_sql_file.read()
        with open(SQL_GET_DB_TABLES_FILEPATH) as get_db_tables_sql_file:
            self.__get_db_tables_sql_str = get_db_tables_sql_file.read()
        with open(SQL_RESET_DB_FILEPATH) as reset_db_file:
            self.__reset_db_sql_str = reset_db_file.read()
        print('Retrieved prefab sql scripts.')

        query = self.__conn.execute(self.__get_db_tables_sql_str)
        if 'SYSTEMS' not in (t[0] for t in query.fetchall()):
            self.reset()

    # Recreates all tables, dropping all data (!)
    def reset(self):
        print('Resetting database...')
        self.__conn.executescript(self.__reset_db_sql_str)
        self.__conn.commit()

    def add_system(self, sid: int, edsm_id: int, name: str, x: float, y: float, z: float, population: int,
                   is_populated: bool, government_id: int, government: str, allegiance_id: int, allegiance: str,
                   security_id: int, security: str, primary_economy_id: int, primary_economy: str, power: str,
                   power_state: str, power_state_id: int, needs_permit: bool, updated_at: int,
                   controlling_minor_faction_id: int, controlling_minor_faction: str,
                   reserve_type_id: int, reserve_type: str):
        self.__conn.execute(self.__update_station_sql_str, (sid, edsm_id, name, x, y, z, population, is_populated,
                                                            government_id, government, allegiance_id, allegiance,
                                                            security_id, security, primary_economy_id,
                                                            primary_economy,
                                                            power, power_state, power_state_id, needs_permit,
                                                            updated_at, controlling_minor_faction_id,
                                                            controlling_minor_faction, reserve_type_id,
                                                            reserve_type))
        self.__conn.commit()

    def add_systems(self, systems: List[Tuple[int, int, str, float, float, float, int, bool, int, str, int, str, int,
                                              str, int, str, str, str, int, bool, int, int, str, int, str]]):
        print('Adding %i system rows...' % len(systems))
        self.__conn.executemany(self.__update_station_sql_str, systems)
        self.__conn.commit()
        print('Done.')

    def get_system_by_id(self, sid: int):
        select_sql_str = ("SELECT id, edsm_id, name, x, y, z, population, is_populated, government_id, government, "
                          "allegiance_id, allegiance, security_id, security, primary_economy_id, primary_economy, "
                          "power, power_state, power_state_id, needs_permit, updated_at, controlling_minor_faction_id, "
                          "controlling_minor_faction, reserve_type_id, reserve_type "
                          "FROM SYSTEMS WHERE id = ?")
        query = self.__conn.execute(select_sql_str, [sid])
        result = query.fetchone()
        return System(*result)

    def get_system_by_name(self, name: str):
        select_sql_str = ("SELECT id, edsm_id, name, x, y, z, population, is_populated, government_id, government, "
                          "allegiance_id, allegiance, security_id, security, primary_economy_id, primary_economy, "
                          "power, power_state, power_state_id, needs_permit, updated_at, controlling_minor_faction_id, "
                          "controlling_minor_faction, reserve_type_id, reserve_type "
                          "FROM SYSTEMS WHERE name = ?")
        query = self.__conn.execute(select_sql_str, [name])
        result = query.fetchone()
        return System(*result)

    def __del__(self):
        self.__conn.close()
        print('Connection to database closed.')
