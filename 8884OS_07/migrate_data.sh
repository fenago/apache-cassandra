#!/bin/sh

# take a snapshot of fenagocdma keyspace
nodetool snapshot fenagocdma

# record the snapshot id
export CASSANDRA_SNAPSHOT_ID=<record the value as shown in the output of the above command>

# copy all snapshot SSTables to a temporary directory
mkdir ~/temp/
mkdir ~/temp/fenagocdma/
mkdir ~/temp/fenagocdma/alert_by_date/
mkdir ~/temp/fenagocdma/alertlist/
mkdir ~/temp/fenagocdma/quote/
mkdir ~/temp/fenagocdma/watchlist/
sudo cp -fenagocdma /var/lib/cassandra/data/fenagocdma/alert_by_date/snapshots/$CASSANDRA_SNAPSHOT_ID/* ~/temp/fenagocdma/alert_by_date/
sudo cp -fenagocdma /var/lib/cassandra/data/fenagocdma/alertlist/snapshots/$CASSANDRA_SNAPSHOT_ID/* ~/temp/fenagocdma/alertlist/
sudo cp -fenagocdma /var/lib/cassandra/data/fenagocdma/quote/snapshots/$CASSANDRA_SNAPSHOT_ID/* ~/temp/fenagocdma/quote/
sudo cp -fenagocdma /var/lib/cassandra/data/fenagocdma/watchlist/snapshots/$CASSANDRA_SNAPSHOT_ID/* ~/temp/fenagocdma/watchlist/

# create keyspace in the production cluster
cqlsh ubtc01
CREATE KEYSPACE fenagocdma WITH replication = {'class': 'NetworkTopologyStrategy',  'NY1': '2'};

# create tables in the production cluster
CREATE TABLE fenagocdma.alert_by_date (
  price_time timestamp,
  symbol varchar,
  signal_price float,
  stock_name varchar,
  PRIMARY KEY (price_time, symbol));
CREATE TABLE fenagocdma.alertlist (
  symbol varchar,
  price_time timestamp,
  signal_price float,
  stock_name varchar,
  PRIMARY KEY (symbol, price_time));
CREATE TABLE fenagocdma.quote (
  symbol varchar,
  price_time timestamp,
  close_price float,
  high_price float,
  low_price float,
  open_price float,
  stock_name varchar,
  volume double,
  PRIMARY KEY (symbol, price_time));
CREATE TABLE fenagocdma.watchlist (
  watch_list_code varchar,
  symbol varchar,
  PRIMARY KEY (watch_list_code, symbol));
exit;

# load SSTable back to the production cluster
cd ~/temp/
sstableloader -d ubtc01 fenagocdma/alert_by_date
sstableloader -d ubtc01 fenagocdma/alertlist
sstableloader -d ubtc01 fenagocdma/quote
sstableloader -d ubtc01 fenagocdma/watchlist

# check the data in cqlsh
cqlsh
select * from fenagocdma.alert_by_date;
select * from fenagocdma.alertlist;
select * from fenagocdma.quote;
select * from fenagocdma.watchlist;
exit;
