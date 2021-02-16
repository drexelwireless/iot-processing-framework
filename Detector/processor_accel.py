from processor import *
import pandas as pd
import time
import operator
import math
import threading
import scipy.signal
import numpy as np
             
class AccelProcessor(Processor):
    def __init__(self):
        super(AccelProcessor, self).__init__()
        self.rssi = []
        self.times = []

    # return a dict with data, title, xlabel, ylabel, X and Y (X/Y and xlabel/ylabel are parallel arrays of x and y keys to be found within data), and each subkey within data is a parallel array of values
    def get_data(self):
        result = dict()
        result['data'] = dict()
        result['title'] = 'Accel Positions'
        result['xlabel'] = ['xval']
        result['ylabel'] = ['yval']
        result['X'] = ['xval']
        result['Y'] = ['yval']
        arrlen = min(len(self.xvals), len(self.yvals))
        result['data']['xval'] = self.xvals[:arrlen]
        result['data']['yval'] = self.yvals[:arrlen]
                        
        return result
                    
    def process_loop(self):                   
        mintime = 0
      
        while not (self.done):            
            if not ('relative_timestamp' in self.df):
                continue
 
            maxtime = self.max_relative_timestamp
            mintime = max(0, maxtime - self.timescale)
            
            if maxtime - mintime < self.timescale:
                time.sleep(0.5)
                continue
             
            try:
                rows = self.df.query('relative_timestamp >= ' + str(mintime) + ' and relative_timestamp <= ' + str(maxtime))
            except:
                continue
         
            for i, row in rows.iterrows():
                print(row['xval'], row['yval'])
                
                self.xvals.append(float(row['xval']))
                self.yvals.append(int(row['yval']))       
             
            time.sleep(1)