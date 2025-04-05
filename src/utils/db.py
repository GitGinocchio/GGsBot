from cachetools import TTLCache
#from redis import Redis            # Piu' avanti potro' usare un client Redis per ora una semplice cache in memoria
import traceback
import aiosqlite
import sqlite3
import asyncio
import inspect
import json
import time
import os

from os.path import join, dirname
from nextcord import Guild, Member
from datetime import datetime, timezone

from .config import config
from .commons import Extensions
from .terminal import getlogger
from .exceptions import *

logger = getlogger("Database")

class Database:
    _instance = None

    def __init__(self, cache_size : int = 1000, cache_ttl : float = 3600, loop : asyncio.AbstractEventLoop = None):
        self._connection : aiosqlite.Connection
        self._cursor : aiosqlite.Cursor
        self._caller_line = None
        self._caller = None

    def __new__(cls, cache_size = 1000, cache_ttl = 3600, loop = None):
        """Initialize database one time"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.db_path = config["paths"]["db"]
            cls._instance.script_path = config["paths"]["db_script"]
            cls._instance.migrations_path = config['paths']['db_migrations']
            cls._instance._connection = None
            cls._instance._cursor = None
            cls._instance._cache = TTLCache(maxsize=cache_size, ttl=cache_ttl)
            cls._cache_ttl = cache_ttl
            cls._instance._start_time = 0
            cls._instance._lock = asyncio.Lock()
            cls._instance._loop = loop
            cls._num_queries = 0
            cls._instance._initialize_db()
        return cls._instance
    
    def _initialize_db(self):
        try:
            conn = sqlite3.connect(self.db_path)
            with open(self.script_path, 'r') as f:
                cursor = conn.executescript(f.read())

                if cursor.rowcount > 0: logger.info("Database created successfully.")

            logger.info("Database initialized.")

            self._apply_migrations(conn)

        except Exception as e:
            conn.rollback()
            logger.error(traceback.format_exc())
        finally:
            conn.close()

    def _apply_migrations(self, conn : sqlite3.Connection):
        try:
            db_backup_path = str(dirname(config['paths']['db'])) + '/database_backup.db'

            with open(config['paths']['db'], 'rb') as dbf:
                content = dbf.read()
                with open(db_backup_path, 'wb') as new_dbf:
                    new_dbf.write(content)

            placeholder_line = '-- This file is used to update the database structure to the latest version before using it.\n-- EDIT ONLY IF YOU KNOW WHAT YOU ARE DOING!'
            with open(self.migrations_path, 'r+') as f:
                content = f.read()

                if content != placeholder_line:
                    conn.executescript(content)

                    logger.warning("Database migrations completed successfully.")

                    if not config['DEBUG_MODE']:
                        f.seek(0)
                        f.truncate()
                    
                        f.write(placeholder_line)
                    else:
                        logger.debug("Database migrations file not deleted because of DEBUG_MODE.")
                else:
                    logger.info("No database migrations were needed.")

            os.remove(db_backup_path)
        except sqlite3.Error as e:
            conn.rollback()
            os.remove(config['paths']['db'])
            os.rename(db_backup_path, config['paths']['db'])
            logger.warning(f"An error occurred while executing migrations:\n{traceback.format_exc()}")
        else:
            conn.commit()

    @property
    def connection(self) -> aiosqlite.Connection:
        if not self._connection or not self._connection.is_alive(): raise RuntimeError("Connection not initialized")
        return self._connection
    
    @property
    def cursor(self) -> aiosqlite.Cursor:
        if not self._cursor: raise RuntimeError("Cursor not initialized")
        return self._cursor

    @property
    def num_queries(self) -> int: 
        return self._num_queries

    async def execute(self, query: str, params: tuple = ()):
        try:
            logger.debug(f'executing query: {query} with params: {params}')
            cursor = await self.cursor.execute(query, params)
        except Exception as e:
            raise e
        else:
            return cursor
        finally:
            self._num_queries += 1
    
    async def executeScript(self, script : str, autocommit : bool = False):
        logger.debug(f'executing script: {script}')
        cursor = await self.cursor.executescript(script)
        if autocommit: await self.connection.commit()
        return cursor

    async def __aenter__(self):
        await self._lock.acquire()

        frame = inspect.currentframe()
        if frame and frame.f_back:
            info = inspect.getframeinfo(frame.f_back)
            self._caller = os.path.basename(info.filename)
            self._caller_line = info.lineno
        else:
            self._caller = "Undefined"
            self._caller_line = "Undefined"

        self._start_time = time.perf_counter()
        logger.debug(f"entering context ({self._caller}:{self._caller_line})")
        
        await self.connect()
    
        self._cursor = await self.connection.cursor()

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        elapsed_time = time.perf_counter() - self._start_time
        logger.debug(f"leaving context ({self._caller}:{self._caller_line} in {elapsed_time:.4f} seconds)")
        await self.cursor.close()

        self._lock.release()

    async def connect(self):
        if self._connection is None or not self._connection.is_alive():
            self._connection = await aiosqlite.connect(self.db_path, loop=self._loop)

    async def close(self):
        if self._cursor:
            await self._cursor.close()

        if self._connection and self._connection.is_alive():
            await self._connection.close()

    # Guilds

    async def getAllGuildIds(self) -> set[int]:
        cursor = await self.execute("SELECT guild_id FROM guilds")
        rows = await cursor.fetchall()

        return set(row[0] for row in rows)
 
    async def hasGuild(self, guild : Guild) -> bool:
        cursor = await self.execute("SELECT 1 FROM guilds WHERE guild_id = ?", (guild.id,))
        result = await cursor.fetchone()
        return result is not None

    async def newGuild(self, guild : Guild) -> None:
        query = """
        INSERT INTO guilds (guild_id, guild_join_date, guild_last_update, guild_name, guild_owner, guild_member_count, guild_bots_count, guild_roles_count, guild_description, guild_premium_tier, guild_premium_subscription_count)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        try:

            dt_format = "%d/%m/%Y, %H:%M:%S"
            cursor = await self.execute(query, (
                guild.id,
                guild.me.joined_at.strftime(dt_format) if guild.me.joined_at else None,
                datetime.now(timezone.utc).strftime(dt_format),
                guild.name,
                guild.owner_id,
                guild.member_count,
                len(guild.bots),
                len(guild.roles),
                guild.description,
                guild.premium_tier,
                guild.premium_subscription_count
            ))

            await self.connection.commit()
        except sqlite3.IntegrityError as e:
            await self.connection.rollback()
            raise DatabaseException("DuplicateRecordError")
        except Exception as e:
            await self.connection.rollback()
            logger.error(e)
            raise e

    async def delGuild(self, guild : Guild | int) -> None:
        queries = [
            "DELETE FROM guilds WHERE guild_id = ?",
            "DELETE FROM extensions WHERE guild_id = ?",
            "DELETE FROM users WHERE guild_id = ?"
        ]

        try:
            for query in queries:
                cursor = await self.execute(query, (guild.id if type(guild) == Guild else guild,))


            await self.connection.commit()
        except DatabaseException as e:
            await self.connection.rollback()
            raise e
        except Exception as e:
            logger.error(e)
            await self.connection.rollback()
            raise e

    async def adjustGuildMemberCount(self, guild: Guild, delta: int, override : bool = False) -> None:
        query = f"""
        UPDATE guilds
        SET guild_member_count = {'guild_member_count + ?' if not override else '?'}, 
            guild_last_update = ?
        WHERE guild_id = ?
        """
        
        try:
            dt_format = "%d/%m/%Y, %H:%M:%S"
            cursor = await self.execute(query, (delta, datetime.now(timezone.utc).strftime(dt_format), guild.id))

            if cursor.rowcount == 0: raise DatabaseException("RecordNotFoundError")
        
            await self.connection.commit()
        except DatabaseException as e:
            await self.connection.rollback()
            raise e
        except Exception as e:
            await self.connection.rollback()
            logger.error(e)
            raise e

    # Users

    async def hasUser(self, user : Member) -> None:
        cursor = await self.execute("SELECT 1 FROM users WHERE user_id = ? AND guild_id = ?", (user.id, user.guild.id))
        result = await cursor.fetchone()
        return result is not None

    async def newUser(self, user : Member, config : dict = {}) -> None:
        query = """
        INSERT INTO users (guild_id, user_id, level, config)
        VALUES (?, ?, ?, ?)
        """

        try:
            cursor = await self.execute(query, (user.guild.id, user.id, 0, json.dumps(config)))
        except aiosqlite.IntegrityError as e:
            await self.connection.rollback()
            raise DatabaseException("DuplicateRecordError")
        else:
            await self.connection.commit()

    async def getUserConfig(self, user : Member) -> dict:
        query = """SELECT config FROM users WHERE guild_id = ? AND user_id = ?"""

        try:
            cursor = await self.execute(query, (user.guild.id, user.id))
            result = await cursor.fetchone()
            if result is None: 
                await self.newUser(user, {})
                return {}
        except aiosqlite.IntegrityError as e:
            await self.connection.rollback()
            logger.error(e)
            raise e
        else:
            return json.loads(result[0])

    async def editUserConfig(self, user : Member, config : dict) -> None:
        query = """
        UPDATE users
        SET config = ?
        WHERE guild_id = ? AND user_id = ?
        """

        try:
            cursor = await self.execute(query, (json.dumps(config), user.guild.id, user.id))

            if cursor.rowcount == 0: await self.newUser(user, config)

            # Da aggiungere questa logica
            # if cursor.rowcount == 0: raise ExtensionException("Not Configured")
        except aiosqlite.IntegrityError as e:
            await self.connection.rollback()
            raise DatabaseException("DuplicateRecordError")
        else:
            await self.connection.commit()

    async def delUser(self, user : Member) -> None:
        query = """DELETE FROM users WHERE guild_id = ? AND user_id = ?"""

        try:
            cursor = await self.execute(query, (user.guild.id, user.id))

            # Da aggiungere questa logica
            # if cursor.rowcount == 0: raise ExtensionException("Not Configured")
        except aiosqlite.Error as e:
            await self.connection.rollback()
            raise e
        else:
            await self.connection.commit()

    # Extensions
    async def setupExtension(self, guild : Guild, extension : Extensions, config : dict) -> None:
        query = """
        INSERT INTO extensions (guild_id, extension_id, enabled, config)
        VALUES (?, ?, ?, ?)
        """

        try:
            await self.execute(query, (guild.id, extension.value, True, json.dumps(config)))

            await self.connection.commit()
        except sqlite3.IntegrityError as e:
            await self.connection.rollback()
            raise ExtensionException("Already Configured")
        except Exception as e:
            await self.connection.rollback()
            logger.error(e)
            raise e

    async def teardownExtension(self, guild : Guild, extension : Extensions) -> None:
        query = """DELETE FROM extensions WHERE guild_id = ? AND extension_id = ?"""

        try:
            cursor = await self.execute(query, (guild.id, extension.value))

            if cursor.rowcount == 0: raise ExtensionException("Not Configured")
        

            await self.connection.commit()
        except ExtensionException as e:
            await self.connection.rollback()
            raise e
        except Exception as e:
            await self.connection.rollback()
            logger.error(e)
            raise e

    async def setExtension(self, guild : Guild, extension : Extensions, enabled : bool) -> None:
        update_query = """
        UPDATE extensions
        SET enabled = ?
        WHERE guild_id = ? AND extension_id = ?
        """

        try:
            await self.execute(update_query, (enabled, guild.id, extension.value))

            await self.connection.commit()
        except sqlite3.IntegrityError as e:
            await self.connection.rollback()
            raise e
        except Exception as e:
            logger.error(e)
            await self.connection.rollback()
            raise e

    async def hasExtension(self, guild : Guild, extension : Extensions) -> bool:
        cursor = await self.execute("SELECT 1 FROM extensions WHERE guild_id = ? AND extension_id = ?", (guild.id,extension.value))
        result = await cursor.fetchone()
        return result is not None

    async def getExtensionConfig(self, guild : Guild, extension : Extensions) -> tuple[dict, bool]:
        query = """SELECT config, enabled FROM extensions WHERE guild_id = ? AND extension_id = ?"""

        try:
            cursor = await self.execute(query, (guild.id, extension.value))
            result = await cursor.fetchone()

            if result is None: raise ExtensionException("Not Configured")

        except ExtensionException as e:
            await self.connection.rollback()
            raise e
        except Exception as e:
            logger.error(e)
            await self.connection.rollback()
            raise e
        else:
            return json.loads(result[0]), result[1] == 1

    async def getAllExtensionConfig(self, extension : Extensions | None = None, guild : Guild | None = None) -> list[tuple[int, str, bool, dict]]:
        if guild and extension:
            query = """SELECT guild_id, extension_id, enabled, config FROM extensions WHERE extension_id = ? AND guild_id = ?"""
            params = (extension.value,guild.id)
        if guild:
            query = """SELECT guild_id, extension_id, enabled, config FROM extensions WHERE guild_id = ?"""
            params = (guild.id,)
        if extension:
            query = """SELECT guild_id, extension_id, enabled, config FROM extensions WHERE extension_id = ?"""
            params = (extension.value,)
        else:
            query = """SELECT guild_id, extension_id, enabled, config FROM extensions"""
            params = ()
        
        try:
            cursor = await self.execute(query, params)
            rows = await cursor.fetchall()
        except Exception as e:
            logger.error(e)
            await self.connection.rollback()
            raise e
        else:
            return list((row[0],row[1], row[2], json.loads(row[3])) for row in rows)

    async def editExtensionConfig(self, guild : Guild, extension : Extensions, updated_values : str | dict) -> None:
        update_query = """
        UPDATE extensions
        SET config = ?
        WHERE guild_id = ? AND extension_id = ?
        """
        
        try:
            if isinstance(updated_values, dict):
                updated_values = json.dumps(updated_values)

            cursor = await self.execute(update_query, (updated_values, guild.id, extension.value))

            if cursor.rowcount == 0: raise ExtensionException("Not Configured")

            await self.connection.commit()
        except ExtensionException as e:
            await self.connection.rollback()
            raise e
        except Exception as e:
            logger.error(e)
            await self.connection.rollback()
            raise e

    async def editAllExtensionConfig(self, updated_values: list[tuple[int, str, bool, dict]]) -> None:
        update_query = """
        UPDATE extensions
        SET config = ?
        WHERE guild_id = ? AND extension_id = ?
        """

        try:
            for guild_id, extension_id, enabled, config in updated_values:
                serialized_config = json.dumps(config)
                await self.execute(update_query, (serialized_config, guild_id, extension_id))

            await self.connection.commit()
        except Exception as e:
            logger.error(e)
            await self.connection.rollback()
            raise e