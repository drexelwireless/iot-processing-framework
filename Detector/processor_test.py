from processor import *
import pandas as pd
import time
import operator
import math
import threading
import scipy.signal
import numpy as np
             
class TestProcessor(Processor):
    def __init__(self):
        super(TestProcessor, self).__init__()
        self.rssi = []
        self.times = []

    # return a dict with data, title, xlabel, ylabel, X and Y (X/Y and xlabel/ylabel are parallel arrays of x and y keys to be found within data), and each subkey within data is a parallel array of values
    def get_data(self):
        result = dict()
        result['data'] = dict()
        result['title'] = 'RSSI'
        result['xlabel'] = ['Time']
        result['ylabel'] = ['RSSI']
        result['X'] = ['timestamp']
        result['Y'] = ['rssi']
        rssilen = min(len(self.times), len(self.rssi))
        result['data']['timestamp'] = self.times[:rssilen]
        result['data']['rssi'] = self.rssi[:rssilen]
                        
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
                print(row['relative_timestamp'], row['rssi'])
                
                self.rssi.append(float(row['rssi']))
                self.times.append(int(row['relative_timestamp']))       
             
            time.sleep(1)