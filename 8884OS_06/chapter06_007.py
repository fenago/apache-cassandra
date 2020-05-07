# -*- coding: utf-8 -*-
# program: chapter06_007.py

## import Cassandra driver library
from cassandra.cluster import Cluster

import pandas as pd
import numpy as np
import datetime

## execute CQL statement to retrieve rows of
## How many alerts were generated on a particular stock over
## a specified period of time?
def alert_over_daterange(ss, sym, sd, ed):
    ## CQL to select data, ? is the placeholder for parameters
    select_cql = "SELECT * FROM alertlist WHERE symbol=? " + \
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
        cols = np.append(cols, [r.symbol, r.stock_name, \
                         r.signal_price])

    ## reshape the 1-D array into a 2-D array for each day
    cols = cols.reshape(idx.shape[0], 3)

    ## convert the arrays into a pandas DataFrame
    df = pd.DataFrame(cols, index=idx, \
                      columns=['symbol', 'stock_name', \
                      'signal_price'])
    return df

def testcase001():
    ## create Cassandra instance
    cluster = Cluster()
    
    ## establish Cassandra connection, using local default
    session = cluster.connect()
    
    ## use fenagocdma keyspace
    session.set_keyspace('fenagocdma')

    ## scan buy-and-hold signals for GS
    ## over 1 month since 28-Jun-2012
    symbol = 'GS'
    start_date = datetime.datetime(2012, 6, 28)
    end_date = datetime.datetime(2012, 7, 28)
    
    ## retrieve alerts
    alerts = alert_over_daterange(session, symbol, \
                                  start_date, end_date)
    
    for index, r in alerts.iterrows():
        print (index.date(), '\t', \
            r['symbol'], '\t', \
            r['stock_name'], '\t', \
            r['signal_price'])
    
    ## close Cassandra connection
    cluster.shutdown()

testcase001()
