DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS posts;

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    username TEXT NOT NULL,
    hash TEXT NOT NULL
);

CREATE UNIQUE INDEX username
    ON users (username);

CREATE TABLE posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    user_id INTEGER NOT NULL,
    created TIMESTAMP NOT NULL,
    title TEXT NOT NULL,
    subtitle TEXT NOT NULL,
    content TEXT NOT NULL
);

--CREATE TABLE posts (
--    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
--    user_id INTEGER NOT NULL,
--    username TEXT NOT NULL,
--    created TIMESTAMP NOT NULL,
--    title TEXT NOT NULL,
--    subtitle TEXT NOT NULL,
--    content TEXT NOT NULL
--);

CREATE UNIQUE INDEX id
    ON posts (id);
