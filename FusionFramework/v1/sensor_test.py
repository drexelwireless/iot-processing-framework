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
import matplotlib.pyplot as plt
        
class TestSensor(Sensor):
    def __init__(self):
        super(TestSensor, self).__init__()

    def start(self, body):
        super(TestSensor, self).start(body)
        
        print(self.df)
        
        rows = self.df.query('relative_timestamp >= 0')
        rows = self.constantdeltat(rows, deltat=str(int(0.04 * self.timescale)) + 'U')
        
        vals = []
        vals2 = []
        times = []
        for i, row in rows.iterrows(): 
            print(row['relative_timestamp'], row['rssi_from_mean'])
            vals.append(float(row['prx_moving_parts_deoscillated']))
            vals2.append(float(row['prx_moving_parts']))
            times.append(float(row['relative_timestamp']))

        ax1 = plt.subplot(211)
        ax2 = plt.subplot(212, sharex=ax1)    
        ax1.plot(times, vals)
        ax2.plot(times, vals2)
        plt.show()
