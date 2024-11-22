from cachetools import TTLCache
#from redis import Redis            # Piu' avanti potro' usare un client Redis per ora una semplice cache in memoria
from typing import Callable
from functools import wraps
import aiosqlite
import sqlite3
import asyncio
import inspect
import hashlib
import json
import time
import uuid
import os

from nextcord import Guild
from datetime import datetime, timezone

from .commons import Extensions
from .terminal import getlogger
from .exceptions import *

logger = getlogger("Database")

class Database:
    _instance = None
    _cache = None

    def __init__(self, db_path = './data/database.db', script_path = './config/database.sql', cache_size : int = 1000, cache_ttl : float = 3600):
        self.db_path = db_path
        self.script_path = script_path
        self._connection = None
        self._start_time = 0
        self._caller = None
        self._caller_line = None
        self._cache_ttl = cache_ttl
        self._cache = TTLCache(maxsize=cache_size, ttl=cache_ttl)
        self._lock = asyncio.Lock()

    def __new__(cls, db_path : str = './data/database.db', script_path : str = './config/database.sql', cache_size : int = 1000, cache_ttl : float = 3600):
        """Initialize database one time"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.db_path = db_path
            cls._instance.script_path = script_path
            cls._instance._initialize_db()
            logger.info("Database initialized")
        return cls._instance
    
    def _initialize_db(self):
        conn = sqlite3.connect(self.db_path)
        with open(self.script_path, 'r') as f:
            conn.executescript(f.read())
        conn.close()

    @property
    def connection(self) -> aiosqlite.Connection:
        assert self._connection and self._connection.is_alive(), "Connection not initialized"
        return self._connection
    
    """
    @classmethod
    def _ttl_cache(cls):
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(self, *args, **kwargs):
                # Crea una chiave univoca per i parametri passati alla funzione
                cache_key = hashlib.md5(f"{args}{kwargs}".encode()).hexdigest()

                # Verifica se la chiave esiste nella cache e se è valida (TTL non scaduto)
                if cache_key in cls._cache:
                    cached_value, timestamp = cls._cache[cache_key]
                    if time.time() - timestamp < cls._cache_ttl:
                        return cached_value  # Restituisci il valore dalla cache se è ancora valido

                # Se il valore non è in cache o il TTL è scaduto, esegui la funzione
                result = await func(self, *args, **kwargs)

                # Memorizza il risultato nella cache con il timestamp
                cls._cache[cache_key] = (result, time.time())
                return result
            return wrapper
        return decorator

    @classmethod
    def _remove_from_ttl_cache(cls):
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(self, *args, **kwargs):
                # Crea una chiave univoca per i parametri passati alla funzione
                cache_key = hashlib.md5(f"{args}{kwargs}".encode()).hexdigest()

                cls._cache.pop(cache_key)

                result = await func(self, *args, **kwargs)

                return result
            return wrapper
        return decorator
    """

    async def __aenter__(self):
        frame = inspect.currentframe().f_back
        info = inspect.getframeinfo(frame)
        self._caller = os.path.basename(info.filename)
        self._caller_line = info.lineno

        self._start_time = time.perf_counter()
        logger.debug(f"entering context ({self._caller}:{self._caller_line})")
        await self.connect()

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        elapsed_time = time.perf_counter() - self._start_time
        logger.debug(f"leaving context ({self._caller}:{self._caller_line} in {elapsed_time:.4f} seconds)")
        #await self.close()

    async def connect(self):
        if self._connection is None or not self._connection.is_alive():
            self._connection = await aiosqlite.connect(self.db_path)

    async def close(self):
        if self._connection and self._connection.is_alive():
            await self._connection.close()

    async def getAllGuildIds(self) -> list[int]:
        cursor = await self.connection.execute("SELECT guild_id FROM guilds")
        rows = await cursor.fetchall()

        await cursor.close()

        self._cache['']

        return [row[0] for row in rows]
 
    async def hasGuild(self, guild : Guild) -> bool:
        cursor = await self.connection.execute("SELECT 1 FROM guilds WHERE guild_id = ?", (guild.id,))
        result = await cursor.fetchone()
        
        await cursor.close()

        return result is not None
    
    async def newGuild(self, guild : Guild) -> None:
        """Aggiungi una guild nel database (assumendo che guild_data contenga tutti i campi necessari)."""
        query = """
        INSERT INTO guilds (guild_id, guild_join_date, guild_last_update, guild_name, guild_owner, guild_member_count, guild_bots_count, guild_roles_count, guild_description, guild_premium_tier, guild_premium_subscription_count)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        try:

            dt_format = "%d/%m/%Y, %H:%M:%S"
            cursor = await self.connection.execute(query, (
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
            await cursor.close()
            await self.connection.commit()
        except sqlite3.IntegrityError as e:
            await self.connection.rollback()
            raise DatabaseException("DuplicateRecordError")

    async def delGuild(self, guild : Guild) -> None:
        query = """DELETE FROM guilds WHERE guild_id = ?"""

        try:
            cursor = await self.connection.execute(query, (guild.id,))

            if cursor.rowcount == 0: raise DatabaseException("RecordNotFoundError")

            await cursor.close()
            await self.connection.commit()
        except Exception as e:
            await self.connection.rollback()
            raise e

    async def adjustGuildMemberCount(self, guild: Guild, delta: int) -> None:
        query = """
        UPDATE guilds
        SET guild_member_count = guild_member_count + ?
        SET guild_last_update = ?
        WHERE guild_id = ?
        """
        
        try:
            cursor = await self.connection.execute(query, (delta, str(datetime.now(timezone.utc)), guild.id))

            if cursor.rowcount == 0: raise DatabaseException("RecordNotFoundError")
        
            await cursor.close()
            await self.connection.commit()
        except Exception as e:
            await self.connection.rollback()
            raise e

    async def setupExtension(self, guild : Guild, extension : Extensions, config : dict) -> None:
        query = """
        INSERT INTO extensions (guild_id, extension_id, config)
        VALUES (?, ?, ?)
        """

        try:
            cursor = await self.connection.execute(query, (guild.id, extension.value, json.dumps(config)))
            await cursor.close()
            await self.connection.commit()
        except sqlite3.IntegrityError as e:
            await self.connection.rollback()
            raise ExtensionException("Already Configured")
        
    async def teardownExtension(self, guild : Guild, extension : Extensions) -> None:
        query = """DELETE FROM extensions WHERE guild_id = ? AND extension_id = ?"""

        try:
            cursor = await self.connection.execute(query, (guild.id, extension.value))

            if cursor.rowcount == 0: raise ExtensionException("Not Configured")
        
            await cursor.close()
            await self.connection.commit()
        except Exception as e:
            await self.connection.rollback()
            raise e

    async def getExtensionConfig(self, guild : Guild, extension : Extensions) -> dict:
        query = """SELECT config FROM extensions WHERE guild_id = ? AND extension_id = ?"""
        cursor = await self.connection.execute(query, (guild.id, extension.value))
        result = await cursor.fetchone()

        await cursor.close()

        if result is None: raise ExtensionException("Not Configured")

        return json.loads(result[0])

    async def getAllExtensionConfig(self, extension : Extensions | None = None) -> list[tuple[int, dict]]:
        if extension is not None:
            query = """SELECT guild_id, config FROM extensions WHERE extension_id = ?"""
            params = (extension.value,)
        else:
            query = """SELECT guild_id, config FROM extensions"""
            params = ()

        async with self.connection.execute(query, params) as cursor:
            rows = await cursor.fetchall()

        return [(row[0], json.loads(row[1])) for row in rows]

    async def editExtensionConfig(self, guild : Guild, extension : Extensions, updated_values : str | dict) -> None:
        update_query = """
        UPDATE extensions
        SET config = ?
        WHERE guild_id = ? AND extension_id = ?
        """
        
        try:
            if isinstance(updated_values, dict):
                updated_values = json.dumps(updated_values)

            cursor = await self.connection.execute(update_query, (updated_values, guild.id, extension.value))
            await cursor.close()
            await self.connection.commit()
        except Exception as e:
            await self.connection.rollback()
            raise e
        
    async def editAllExtensionConfig(self, extension: Extensions, updated_values: list[tuple[int, dict]]) -> None:
        update_query = """
        UPDATE extensions
        SET config = ?
        WHERE guild_id = ? AND extension_id = ?
        """

        try:
            for guild_id, config in updated_values:
                serialized_config = json.dumps(config)
                await self.connection.execute(update_query, (serialized_config, guild_id, extension.value))

            await self.connection.commit()
        except Exception as e:
            await self.connection.rollback()
            raise e