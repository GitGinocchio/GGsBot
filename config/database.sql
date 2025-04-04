BEGIN; 

CREATE TABLE IF NOT EXISTS guilds (
    guild_id INTEGER PRIMARY KEY,
    guild_join_date TEXT,
    guild_last_update TEXT,
    guild_name TEXT,
    guild_owner INTEGER,
    guild_member_count INTEGER,
    guild_bots_count INTEGER,
    guild_roles_count INTEGER,
    guild_description TEXT NULL,
    guild_premium_tier INTEGER,
    guild_premium_subscription_count INTEGER
);

CREATE TABLE IF NOT EXISTS users (
    guild_id INTEGER,
    user_id INTEGER,
    level INTEGER,
    config JSON,
    PRIMARY KEY (user_id, guild_id),                                                  -- Garantiamo che ci sia una sola combinazione di user_id + guild_id
    FOREIGN KEY (guild_id) REFERENCES guilds (guild_id) ON DELETE CASCADE             -- Assicuriamo che il guild_id esista nella tabella guilds
);

CREATE TABLE IF NOT EXISTS extensions (
    guild_id INTEGER,
    config JSON,
    extension_id TEXT,
    enabled BOOLEAN,

    PRIMARY KEY (guild_id, extension_id),                                             -- Garantiamo che ci sia una sola combinazione di guild_id + extension_id
    FOREIGN KEY (guild_id) REFERENCES guilds (guild_id) ON DELETE CASCADE             -- Garantiamo che stiamo inserendo una estensione per una guild esistente
);

COMMIT; 

-- ROLLBACK;                                                                          -- Se qualcosa va storto, annulla tutto