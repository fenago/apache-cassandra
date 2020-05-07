# -*- coding: utf-8 -*-
# program: chapter06_008.py

## import Cassandra driver library
from cassandra.cluster import Cluster

import pandas as pd
import numpy as np
import datetime

## execute CQL statement to retrieve rows of
## How many alerts were generated on a particular stock over
## a specified period of time?
def alert_on_date(ss, dd):
    ## CQL to select data, ? is the placeholder for parameters
    select_cql = "SELECT * FROM alert_by_date WHERE " + \
                 "price_time=?"

    ## prepare select CQL
    select_stmt = ss.prepare(select_cql)

    ## execute the select CQL
    result = ss.execute(select_stmt, [dd])

     ## initialize an index array
    idx = np.asarray([])

    ## initialize an array for columns
    cols = np.asarray([])

    ## loop thru the query resultset to make up the DataFrame
    for r in result:
        idx = np.append(idx, [r.symbol])
        cols = np.append(cols, [r.stock_name, r.price_time, \
                         r.signal_price])

    ## reshape the 1-D array into a 2-D array for each day
    cols = cols.reshape(idx.shape[0], 3)

    ## convert the arrays into a pandas DataFrame
    df = pd.DataFrame(cols, index=idx, \
                      columns=['stock_name', 'price_time', \
                      'signal_price'])
    return df

def testcase001():
    ## create Cassandra instance
    cluster = Cluster()
    
    ## establish Cassandra connection, using local default
    session = cluster.connect()
    
    ## use packtcdma keyspace
    session.set_keyspace('packtcdma')
    
    ## scan buy-and-hold signals for GS over 1 month since 28-Jun-2012
    on_date = datetime.datetime(2012, 7, 13)
    
    ## retrieve alerts
    alerts = alert_on_date(session, on_date)
    
    ## print out alerts
    for index, r in alerts.iterrows():
        print index, '\t', \
              r['stock_name'], '\t', \
              r['signal_price']
    
    ## close Cassandra connection
    cluster.shutdown()

testcase001()
