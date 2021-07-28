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
        
class OutputSensor(Sensor):
    def __init__(self):
        super(OutputSensor, self).__init__()

    def start(self, body):
        super(OutputSensor, self).start(body)
        
        self.df.to_csv('out.csv')
