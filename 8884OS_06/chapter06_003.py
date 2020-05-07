# -*- coding: utf-8 -*-
# program: chapter06_003.py

## import Cassandra driver library
from cassandra.cluster import Cluster

## function to add stock_name column
def add_stockname_to_quote(ss):
    ## add stock_name to quote
    ss.execute('ALTER TABLE quote ' + \
               'ADD stock_name varchar')

## create Cassandra instance
cluster = Cluster()

## establish Cassandra connection, using local default
session = cluster.connect()

## use fenagocdma keyspace
session.set_keyspace('fenagocdma')

## add stock_name column
add_stockname_to_quote(session)

## close Cassandra connection
cluster.shutdown()
