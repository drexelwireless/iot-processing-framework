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
import sklearn.cluster
import threading
from pykalman import KalmanFilter
import matplotlib.pyplot as plt
                
class FusionSensor(Sensor):
    def __init__(self):
        super(FusionSensor, self).__init__()
        
        self.measures = [] # the measure classes
        self.times = []
        self.estimates = []
        self.iteration = 1
        self.iterationsize = 0.5 
        self.fusiongobackn = 12
        self.threadmeasures = False
        
        # Add measure classes to the self.measures array, passing in self
        #self.measures.append(TestMeasure(self))
        
        # Add a Fuser class (or set to None)
        self.fuser = None #MaxlikelihoodFuser()
        
        # Add a Ground Truth class (or set to None)
        self.groundtruth = None #GroundTruth301530sec()
        self.sqerrvector = []
        
        # Add a perturber (or set to None)
        self.perturber = None #RandomPerturber()
        
    def start(self, body):
        if not (self.perturber is None):
            body = self.perturber.perturb(body)
        #print 'len', len(body['data'])
            
        super(FusionSensor, self).start(body)
        
        while self.iteration * self.timescale * self.iterationsize <= self.max_relative_timestamp:
            # Collect the measures
            if self.threadmeasures == True:
                threads = []
                for m in self.measures:
                    t = threading.Thread(target=m.process())
                    threads.append(t)
                    t.start()
            
                # Wait for the measure threads to finish    
                for t in threads:
                    t.join()
                    
                for m in self.measures:
                    m.sqerror(self.groundtruth, self.iteration * self.iterationsize)
            else:
                for m in self.measures:
                    m.process()
                    m.sqerror(self.groundtruth, self.iteration * self.iterationsize)
            
            # Fuse
            if not (self.fuser is None):
                fusedmeasure = self.fuser.fuse(self.measures, self.fusiongobackn)
                
                if not (fusedmeasure is None):
                    self.estimates.append(fusedmeasure)
                    self.times.append(self.iteration * self.timescale * self.iterationsize)
                
                    print(self.times[-1], self.estimates[-1]) 

                    if not (self.groundtruth is None):
                        if self.groundtruth.truth(self.iteration * self.iterationsize) >= 0:
                            self.sqerrvector.append((self.estimates[-1] - self.groundtruth.truth(self.iteration * self.iterationsize))**2)
            
            self.iteration = self.iteration + 1 

        # Print the error report
        if not (self.groundtruth is None):
            for m in self.measures:
                if len(m.sqerrvector) > 0:
                    print('Mean Squared Error for', m.title, ':', math.sqrt(np.sum(m.sqerrvector) * 1.0 / len(m.sqerrvector)), 'Variance:', np.var(m.estimatevector))
            if len(self.sqerrvector) > 0:
                print('Mean Squared Error for Fused Rate:', math.sqrt(np.sum(self.sqerrvector) * 1.0 / len(self.sqerrvector)), 'Variance:', np.var(self.estimates))
            
        # Plot the sensors
        fig = plt.figure(1)
        ax = plt.subplot(len(self.measures)+1, 1, 1)
        plt.plot(self.times, self.estimates, 'r-')
        plt.ylabel('Fused')
        plt.title("Respiratory rate in breaths per minute") # set the title only once, at the very top
        ax.autoscale_view(True,True,True)
        colors = ['g', 'b', 'c', 'm', 'y', 'k', 'r']
        coloridx = 0
        i = 0
        for m in self.measures:
            ax = plt.subplot(len(self.measures)+1, 1, i+2, sharex=ax)
            plt.plot(m.timevector, m.estimatevector, colors[coloridx % len(colors)] + 'o')
            plt.ylabel(m.title)
            ax.autoscale_view(True,True,True)
            coloridx = (coloridx + 1) % len(colors)
            i = i + 1

        # Label the last subplot axes only, since they're all the same
        ax.set_xlabel('Time (Microseconds)')
        
        plt.show()             
        plt.clf()
