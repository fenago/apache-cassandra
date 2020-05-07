# -*- coding: utf-8 -*-
# program: lab07_001.py

## import Cassandra driver library
from cassandra.cluster import Cluster

import pandas as pd
import numpy as np
import datetime

## import Cassandra BatchStatement library
from cassandra.query import BatchStatement
from decimal import *

## function to insert historical data into table quote
## ss: Cassandra session
## sym: stock symbol
## sd: start date
## ed: end date
## return a DataFrame of stock quote
def retrieve_data(ss, sym, sd, ed):
    ## CQL to select data, ? is the placeholder for parameters
    select_cql = "SELECT * FROM quote WHERE symbol=? " + \
                 "AND price_time >= ? AND price_time <= ?"

    ## prepare select CQL
    select_stmt = ss.prepare(select_cql)

    ## execute the select CQL
    result = ss.execute(select_stmt, [sym, sd, ed])

    ## initialize an index array
    idx = np.asarray([])

    ## initialize an array for columns
    cols = np.asarray([])

    ## loop thru the query resultset to make up the DataFrame
    for r in result:
        idx = np.append(idx, [r.price_time])
        cols = np.append(cols, [r.open_price, r.high_price, \
                         r.low_price, r.close_price, \
                         r.volume, r.stock_name])

    ## reshape the 1-D array into a 2-D array for each day
    cols = cols.reshape(idx.shape[0], 6)

    ## convert the arrays into a pandas DataFrame
    df = pd.DataFrame(cols, index=idx, \
                      columns=['open_price', 'high_price', \
                      'low_price', 'close_price', \
                      'volume', 'stock_name'])
    return df

## function to compute a Simple Moving Average on a DataFrame
## d: DataFrame
## prd: period of SMA
## return a DataFrame with an additional column of SMA
def sma(d, prd):
    d['sma'] = d['close_price'].rolling(window=prd).mean()
    return d

## function to apply screening rule to generate buy signals
## screening rule, Close > 10-Day SMA
## d: DataFrame
## return a DataFrame containing buy signals
def signal_close_higher_than_sma10(d):
    return d[d.close_price > d.sma]

## function to retrieve watchlist
## ss: Cassandra session
## ws: watchlist code
def load_watchlist(ss, ws):
    ## CQL to select data, ? is the placeholder for parameters
    select_cql = "SELECT symbol FROM watchlist " + \
                 "WHERE watch_list_code=?"

    ## prepare select CQL
    select_stmt = ss.prepare(select_cql)

    ## execute the select CQL
    result = ss.execute(select_stmt, [ws])

    ## initialize the stock array
    stw = []

    ## loop thru the query resultset to make up the DataFrame
    for r in result:
        stw.append(r.symbol)

    return stw

## function to insert historical data into table quote
## ss: Cassandra session
## sym: stock symbol
## d: standardized DataFrame containing historical data
## sn: stock name
def insert_alert(ss, sym, sd, cp, sn):
    ## CQL to insert data, ? is the placeholder for parameters
    insert_cql1 = "INSERT INTO alertlist (" + \
                 "symbol, price_time, signal_price, stock_name" +\
                 ") VALUES (?, ?, ?, ?)"

    ## CQL to insert data, ? is the placeholder for parameters
    insert_cql2 = "INSERT INTO alert_by_date (" + \
                 "symbol, price_time, signal_price, stock_name" +\
                 ") VALUES (?, ?, ?, ?)"

    ## prepare the insert CQL as it will run repeatedly
    insert_stmt1 = ss.prepare(insert_cql1)
    insert_stmt2 = ss.prepare(insert_cql2)

    ## set decimal places to 4 digits
    getcontext().prec = 4

    ## begin a batch
    batch = BatchStatement()
    
    ## add insert statements into the batch
    batch.add(insert_stmt1, [sym, sd, cp, sn])
    batch.add(insert_stmt2, [sym, sd, cp, sn])
    
    ## execute the batch
    ss.execute(batch)

def testcase003():

    ######################################################################## 
    # We will be running the example on single node in the lab environment # 
    ######################################################################## 

    ## create Cassandra instance
    cluster = Cluster()

    ## create Cassandra instance with multiple nodes
    # cluster = Cluster(['ubtc01', 'ubtc02'])
    
    ## establish Cassandra connection, using local default
    session = cluster.connect('fenagocdma')
    
    start_date = datetime.datetime(2012, 6, 28)
    end_date = datetime.datetime(2013, 9, 28)
    
    ## load the watch list
    stocks_watched = load_watchlist(session, "WS01")
    
    for symbol in stocks_watched:
        ## retrieve data
        data = retrieve_data(session, symbol, start_date, end_date)
        
        ## compute 10-Day SMA
        data = sma(data, 10)
        
        ## generate the buy-and-hold signals
        alerts = signal_close_higher_than_sma10(data)
        
        ## save the alert list
        for index, r in alerts.iterrows():
            insert_alert(session, symbol, index, \
                         Decimal(r['close_price']), \
                         r['stock_name'])
    
    ## close Cassandra connection
    cluster.shutdown()

testcase003()
