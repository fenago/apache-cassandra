# -*- coding: utf-8 -*-
# program: lab05_007.py

import pandas as pd

## function to compute a Simple Moving Average on a DataFrame
## d: DataFrame
## prd: period of SMA
## return a DataFrame with an additional column of SMA
def sma(d, prd):
    d['sma'] = d['close_price'].rolling(window=prd).mean()
    return d
