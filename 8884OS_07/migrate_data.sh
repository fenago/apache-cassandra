#!/bin/sh

# take a snapshot of packtcdma keyspace
nodetool snapshot packtcdma

# record the snapshot id
export CASSANDRA_SNAPSHOT_ID=<record the value as shown in the output of the above command>

# copy all snapshot SSTables to a temporary directory
mkdir ~/temp/
mkdir ~/temp/packtcdma/
mkdir ~/temp/packtcdma/alert_by_date/
mkdir ~/temp/packtcdma/alertlist/
mkdir ~/temp/packtcdma/quote/
mkdir ~/temp/packtcdma/watchlist/
sudo cp -packtcdma /var/lib/cassandra/data/packtcdma/alert_by_date/snapshots/$CASSANDRA_SNAPSHOT_ID/* ~/temp/packtcdma/alert_by_date/
sudo cp -packtcdma /var/lib/cassandra/data/packtcdma/alertlist/snapshots/$CASSANDRA_SNAPSHOT_ID/* ~/temp/packtcdma/alertlist/
sudo cp -packtcdma /var/lib/cassandra/data/packtcdma/quote/snapshots/$CASSANDRA_SNAPSHOT_ID/* ~/temp/packtcdma/quote/
sudo cp -packtcdma /var/lib/cassandra/data/packtcdma/watchlist/snapshots/$CASSANDRA_SNAPSHOT_ID/* ~/temp/packtcdma/watchlist/

# create keyspace in the production cluster
cqlsh ubtc01
CREATE KEYSPACE packtcdma WITH replication = {'class': 'NetworkTopologyStrategy',  'NY1': '2'};

# create tables in the production cluster
CREATE TABLE packtcdma.alert_by_date (
  price_time timestamp,
  symbol varchar,
  signal_price float,
  stock_name varchar,
  PRIMARY KEY (price_time, symbol));
CREATE TABLE packtcdma.alertlist (
  symbol varchar,
  price_time timestamp,
  signal_price float,
  stock_name varchar,
  PRIMARY KEY (symbol, price_time));
CREATE TABLE packtcdma.quote (
  symbol varchar,
  price_time timestamp,
  close_price float,
  high_price float,
  low_price float,
  open_price float,
  stock_name varchar,
  volume double,
  PRIMARY KEY (symbol, price_time));
CREATE TABLE packtcdma.watchlist (
  watch_list_code varchar,
  symbol varchar,
  PRIMARY KEY (watch_list_code, symbol));
exit;

# load SSTable back to the production cluster
cd ~/temp/
sstableloader -d ubtc01 packtcdma/alert_by_date
sstableloader -d ubtc01 packtcdma/alertlist
sstableloader -d ubtc01 packtcdma/quote
sstableloader -d ubtc01 packtcdma/watchlist

# check the data in cqlsh
cqlsh
select * from packtcdma.alert_by_date;
select * from packtcdma.alertlist;
select * from packtcdma.quote;
select * from packtcdma.watchlist;
exit;
