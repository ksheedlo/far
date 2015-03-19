#!/bin/bash

sqlite3 data/sins.sqlite3 <<SuchDatabase
CREATE TABLE IF NOT EXISTS users (
  name TEXT NOT NULL UNIQUE,
  password TEXT NOT NULL,
  response_body TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
  session TEXT,
  service_provider TEXT NOT NULL
);
SuchDatabase
