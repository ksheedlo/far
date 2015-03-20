#!/bin/bash

sqlite3 data/sins.sqlite3 <<SuchDatabase
CREATE TABLE IF NOT EXISTS users (
  name TEXT NOT NULL UNIQUE,
  password TEXT NOT NULL,
  response_body TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
  id INTEGER PRIMARY KEY,
  user_id TEXT NOT NULL,
  session TEXT
);

CREATE TABLE IF NOT EXISTS sp_sessions (
  session_id INT NOT NULL,
  service_provider TEXT NOT NULL,
  FOREIGN KEY(session_id) REFERENCES sessions(id)
);
SuchDatabase
