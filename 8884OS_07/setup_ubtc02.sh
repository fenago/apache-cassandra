#!/bin/sh

# stop cassandra service
sudo service cassandra stop

# remove the system keyspace
sudo rm -rf /var/lib/cassandra/data/system/*

# modify cassandra.yaml
# sudo vi /etc/cassandra/cassandra.yaml

# mosidy cassandra-rackdc.properties
# sudo vi /etc/cassandra/cassandra-rackdc.properties

# start the non-seed node ubtc02
sudo service cassandra start

# check cluster status
nodetool status
