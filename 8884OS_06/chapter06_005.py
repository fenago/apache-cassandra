# -*- coding: utf-8 -*-
# program: lab06_005.py

## import Cassandra driver library
from cassandra.cluster import Cluster
from decimal import *

## web is the shorthand alias of pandas_datareader
import pandas_datareader as web
import datetime

## import BeautifulSoup and requests
from bs4 import BeautifulSoup
import requests

## function to insert historical data into table quote
## ss: Cassandra session
## sym: stock symbol
## d: standardized DataFrame containing historical data
## sn: stock name
def insert_quote(ss, sym, d, sn):
    ## CQL to insert data, ? is the placeholder for parameters
    insert_cql = "INSERT INTO quote (" + \
                 "symbol, price_time, open_price, high_price," + \
                 "low_price, close_price, volume, stock_name" + \
                 ") VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
    ## prepare the insert CQL as it will run repeatedly
    insert_stmt = ss.prepare(insert_cql)

    ## set decimal places to 4 digits
    getcontext().prec = 4

    ## loop thru the DataFrame and insert records
    for index, row in d.iterrows():
        ss.execute(insert_stmt, \
                   [sym, index, \
                   Decimal(row['open_price']), \
                   Decimal(row['high_price']), \
                   Decimal(row['low_price']), \
                   Decimal(row['close_price']), \
                   Decimal(row['volume']), \
                   sn])

## retrieve the historical daily stock quote from Yahoo! Finance
## Parameters
## sym: stock symbol
## sd: start date
## ed: end date
def collect_data(sym, sd, ed):
    ## data is a DataFrame holding the daily stock quote
    data = web.DataReader(sym, 'yahoo', sd, ed)
    return data

## transform received data into standardized format
## Parameter
## d: DataFrame containing Yahoo! Finance stock quote
def transform_yahoo(d):
    ## drop extra column 'Adj Close'
    d1 = d.drop(['Adj Close'], axis=1)

    ## standardize the column names
    ## rename index column to price_date
    d1.index.names=['price_date']

    ## rename the columns to match the respective columns
    d1 = d1.rename(columns={'Open':'open_price', \
                            'High':'high_price', \
                            'Low':'low_price', \
                            'Close':'close_price', \
                            'Volume':'volume'})
    return d1

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

## function to retrieve stock name from Yahoo!Finance
## sym: stock symbol
def get_stock_name(sym):
	url = 'http://finance.yahoo.com/q/hp?s=' + sym + \
          '+Historical+Prices'
	r = requests.get(url)
	soup = BeautifulSoup(r.text)
	data = soup.findAll('h1')
	return data[0].text

def testcase001():
    ## create Cassandra instance
    cluster = Cluster()
    
    ## establish Cassandra connection, using local default
    session = cluster.connect('fenagocdma')
    
    start_date = datetime.datetime(2012, 1, 1)
    end_date = datetime.datetime(2014, 6, 28)
    
    ## load the watchlist
    stocks_watched = load_watchlist(session, "WS01")
    
    ## iterate the watchlist
    for symbol in stocks_watched:
        ## get stock name
        stock_name = get_stock_name(symbol)
    
        ## collect data
        data = collect_data(symbol, start_date, end_date)
    
        ## transform Yahoo! Finance data
        data = transform_yahoo(data)
    
        ## insert historical data
        insert_quote(session, symbol, data, stock_name)
    
    ## close Cassandra connection
    cluster.shutdown()

testcase001()
