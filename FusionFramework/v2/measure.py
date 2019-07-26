import threading
import pandas as pd
import numpy as np
import math
import filterpy.kalman as kf
import scipy.signal
from rfidutil import *
from sensor import *

class Measure(object):
    def __init__(self, _sensor):
        self.sensor = _sensor
        self.estimatevector = []
        self.timevector = []
        self.sqerrvector = []
        self.meanpowers = []
        self.nontrivialmagnitudes = dict()
        self.newmeasureavailable = False # did we take a new measurement the last time we called process?
        self.title = 'Measure'
        self.errvector = []
        
    def spectrogram(self, data, Fs, mintime, noverlap=0):
        #print data
        framelength=len(data)
        
        data = np.asarray(data, dtype='float64')
        
        freqs, times, Sxx = scipy.signal.spectrogram(data, fs=Fs, nperseg=framelength, noverlap=noverlap, detrend='linear')
        freqs_phase, times_phase, Sxx_phase = scipy.signal.spectrogram(data, fs=Fs, nperseg=framelength, noverlap=noverlap, detrend='linear', mode='phase')
        freqs_angle, times_angle, Sxx_angle = scipy.signal.spectrogram(data, fs=Fs, nperseg=framelength, noverlap=noverlap, detrend='linear', mode='angle')
        
        freqtimes = []
        fullfreqs = []
        
        for i in range(len(times)):
            center_relative_timestamp = mintime + (times[i] * self.sensor.timescale)
            
            freqtimes.append(center_relative_timestamp)
            
            powers = []
            angles = []
            phases = []
            
            for j in range(len(Sxx)):
                instant_power = Sxx[j][i]
                freq = freqs[j]
                
                instant_angle = Sxx_angle[j][i]
                instant_phase = Sxx_phase[j][i]
                                   
                #print 'Spectral moment', center_relative_timestamp, instant_power, instant_angle, instant_phase
                
                powers.append(instant_power)
                angles.append(instant_angle)
                phases.append(instant_phase)
                
                fullfreqs.append(freq)
              
        return freqtimes, powers, angles, phases, fullfreqs
    
    def isnontrivialmagnitudebytime(self, iteration, iterationsize, timescale, trainperiod, deltat, confidence, gobacksec, sensor, epctag):
        nontrivialmagnitude = True
        
        timekey = iteration * iterationsize
        
        if timekey < 0:
            return nontrivialmagnitude
        
        if timekey in self.nontrivialmagnitudes:
            return self.nontrivialmagnitudes[timekey]
        
        # capture the first epc96 tag seen so that we only process those; must be done before we do constant delta t or any resampling, because this removes the string values from the query... set epctag prior to this point to override with a specific tag
        if epctag is None:
            rows = sensor.df.query('relative_timestamp >= ' + str(iteration * timescale * iterationsize - gobacksec * timescale) + ' and relative_timestamp < ' + str(iteration * timescale * iterationsize))
            
            if len(rows) <= 0:
                return nontrivialmagnitude
            
            epctag = rows['epc96'][0]
        
        rows = sensor.df.query('relative_timestamp >= ' + str(iteration * timescale * iterationsize - gobacksec * timescale) + ' and relative_timestamp < ' + str(iteration * timescale * iterationsize) + ' and epc96 == \"' + epctag + '\"')
    
        if len(rows) <= 0:
            return nontrivialmagnitude
    
        rows = sensor.constantdeltat(rows, deltat=str(int(deltat * timescale)) + 'U')
    
        signal = []
        for i, row in rows.iterrows(): 
            signal.append(float(row['rssi_from_mean'])) 
        
        signal = sensor.interpnan(signal)
    
        powers = []
        signal = np.asarray(signal, dtype='float64')
        freqs, times, Sxx = scipy.signal.spectrogram(signal, fs=1.0/deltat, nperseg=len(signal), noverlap=0, detrend='linear')
        for i in range(len(times)):
            for j in range(len(Sxx)):
                powers.append(Sxx[j][i])
        power = np.mean(powers)
    
        if iteration * iterationsize < trainperiod:
            self.meanpowers.append(power)
        else:
            t,p = ttest(power, np.mean(self.meanpowers), np.var(self.meanpowers), len(self.meanpowers)) 
        
            if p < 1-confidence and power < np.mean(self.meanpowers): # passes t test, and remove instances in which the sample is smaller than the typical respirating mean (abnormally deep breath is not a cessation anomaly)
                nontrivialmagnitude = False
            
        self.nontrivialmagnitudes[timekey] = nontrivialmagnitude
    
        return nontrivialmagnitude
            
    def isnontrivialmagnitude(self, sensor, trainperiod=30, deltat=0.02, confidence=0.95, gobacksec=0.5, epctag=None, consecutive=8):
        anynontrivial = False
        
        for i in range(consecutive):
            goback = i-1
            
            thisnontrivial = self.isnontrivialmagnitudebytime(sensor.iteration - goback, sensor.iterationsize, sensor.timescale, trainperiod, deltat, confidence, gobacksec, sensor, epctag)
            
            if thisnontrivial == True:
                anynontrivial = True
                break
                
        return anynontrivial
        
    def process(self):
        pass
        
    def sqerror(self, groundtruth, time):
        if not (groundtruth is None):
            if self.newmeasureavailable == True:
                sqerr = (self.estimatevector[-1] - groundtruth.truth(time))**2
                self.sqerrvector.append(sqerr)