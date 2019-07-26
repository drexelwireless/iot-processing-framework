from sensor import *
import pandas as pd
import time
import operator
import math
import threading
import scipy.signal
import numpy as np
import scipy.stats
import csv
        
class Test2Sensor(Sensor):
    def __init__(self):
        super(Test2Sensor, self).__init__()

    def start(self, body):
        super(Test2Sensor, self).start(body)
        
        starttime = 0
        endtime = 1 * self.timescale
        
        while starttime < self.max_relative_timestamp:
            rows = self.df.query('relative_timestamp >= ' + str(starttime) + ' and relative_timestamp < ' + str(endtime))
            # Do NOT resample prior to separating values like antenna/epc, because you will merge those values together even though they cross tag or antenna boundaries
        
            values = dict()
        
            for i, row in rows.iterrows():
                epc = row['epc96']
                prx = row['prx_moving_parts']
            
                if not (epc in values):
                    values[epc] = []
                
                values[epc].append(prx)
            
            for epc in values:
                print('Here are the PRX moving parts values for tag ' + epc)
                print(values[epc])
                
            starttime = starttime + (1 * self.timescale)
            endtime = endtime + (1 * self.timescale)
