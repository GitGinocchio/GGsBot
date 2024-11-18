#from redis import Redis            # Piu' avanti potro' usare un client Redis per ora una semplice cache in memoria
from cachetools import TTLCache
import sqlite3



class Database:
    def __init__(self):
        pass