# -*- coding: utf-8 -*-
# program: lab06_004.py

## import Cassandra driver library
from cassandra.cluster import Cluster

## function to create alert_by_date table
def create_alertbydate(ss):
    ## create alert_by_date table if not exists
    ss.execute('CREATE TABLE IF NOT EXISTS alert_by_date (' + \
               'symbol varchar,' + \
               'price_time timestamp,' + \
               'stock_name varchar,' + \
               'signal_price float,' + \
               'PRIMARY KEY (price_time, symbol))')

## create Cassandra instance
cluster = Cluster()

## establish Cassandra connection, using local default
session = cluster.connect()

## use fenagocdma keyspace
session.set_keyspace('fenagocdma')

## create alert_by_date table
create_alertbydate(session)

## close Cassandra connection
cluster.shutdown()
