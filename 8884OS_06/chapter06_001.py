# -*- coding: utf-8 -*-
# program: chapter06_001.py

## import Cassandra driver library
from cassandra.cluster import Cluster

## function to create watchlist
def create_watchlist(ss):
    ## create watchlist table if not exists
    ss.execute('CREATE TABLE IF NOT EXISTS watchlist (' + \
               'watch_list_code varchar,' + \
               'symbol varchar,' + \
               'PRIMARY KEY (watch_list_code, symbol))')
    
    ## insert AAPL, AMZN, and GS into watchlist
    ss.execute("INSERT INTO watchlist (watch_list_code, " + \
               "symbol) VALUES ('WS01', 'AAPL')")
    ss.execute("INSERT INTO watchlist (watch_list_code, " + \
               "symbol) VALUES ('WS01', 'AMZN')")
    ss.execute("INSERT INTO watchlist (watch_list_code, " + \
               "symbol) VALUES ('WS01', 'GS')")

## create Cassandra instance
cluster = Cluster()

## establish Cassandra connection, using local default
session = cluster.connect()

## use packtcdma keyspace
session.set_keyspace('packtcdma')

## create watchlist table
create_watchlist(session)

## close Cassandra connection
cluster.shutdown()
