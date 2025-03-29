-- This file is used to update the database structure to the latest version before using it.
-- EDIT ONLY IF YOU KNOW WHAT YOU ARE DOING!

PRAGMA foreign_keys = OFF;

ALTER TABLE users RENAME TO old_users;
ALTER TABLE extensions RENAME TO old_extensions;

CREATE TABLE users (
    guild_id INTEGER,
    user_id INTEGER,
    level INTEGER,
    config JSON,
    PRIMARY KEY (user_id, guild_id),
    FOREIGN KEY (guild_id) REFERENCES guilds (guild_id) ON DELETE CASCADE
);

CREATE TABLE extensions (
    guild_id INTEGER,
    config JSON,
    extension_id TEXT,
    enabled BOOLEAN,
    PRIMARY KEY (guild_id, extension_id),
    FOREIGN KEY (guild_id) REFERENCES guilds (guild_id) ON DELETE CASCADE
);

INSERT INTO users (guild_id, user_id, level, config)
SELECT guild_id, user_id, level, config FROM old_users;

INSERT INTO extensions (guild_id, config, extension_id, enabled)
SELECT guild_id, config, extension_id, enabled FROM old_extensions;

DROP TABLE old_users;
DROP TABLE old_extensions;

PRAGMA foreign_keys = ON;