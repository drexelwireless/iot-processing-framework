import threading
import pandas as pd
import numpy as np
import math
import filterpy.kalman as kf
from sklearn import linear_model
from scipy.signal import butter, filtfilt, correlate
from scipy.linalg import block_diag
from statsmodels.tsa.arima_model import ARIMA
#from statsmodels.graphics.tsaplots import plot_acf
from scipy import stats
from rfidutil import *
import json

class RSSIEstimator:
    def __init__(self, initial_prior=0, initial_variance=256):
        self.rssihistory = []
        self.timehistory = []

        self.x = initial_prior
        self.P = initial_variance

    def add_data(self, rssi, timestamp):
        self.rssihistory.append(rssi)
        self.timehistory.append(timestamp)

    def get_current_rssi(self):
        if len(self.rssihistory) == 0:
            return -256, -256

        self.x, self.P = kf.predict(x=self.x, P=self.P, u=0, Q=2) # rely more on the prediction by using a high Q variance
        self.x, self.P = kf.update(x=self.x, P=self.P, z=self.rssihistory[-1], R=1) # measurement variance could be up to 1 per RSSI read

        estimated_rssi = self.x

        #print self.timehistory[-1], estimated_rssi, self.rssihistory[-1]
        return estimated_rssi, self.rssihistory[-1]

class Sensor(object):
    def __init__(self, timescale=1e6, debug=False):
        self.timescale = timescale
        self.df = pd.DataFrame(dtype='float')
        self.max_relative_timestamp = 0
        self.rssi_estimator = RSSIEstimator()
        self.prx_m_p_d_estimator = RSSIEstimator()
        self.debug = debug
        
    def log(self, msg):
        if self.debug:
            print(msg)

    # https://stackoverflow.com/questions/6518811/interpolate-nan-values-in-a-numpy-array        
    def interpnan(self, y):
        def helper(y):
            """Helper to handle indices and logical indices of NaNs.

            Input:
                - y, 1d numpy array with possible NaNs
            Output:
                - nans, logical indices of NaNs
                - index, a function, with signature indices= index(logical_indices),
                  to convert logical indices of NaNs to 'equivalent' indices
            Example:
                >>> # linear interpolation of NaNs
                >>> nans, x= nan_helper(y)
                >>> y[nans]= np.interp(x(nans), x(~nans), y[~nans])
            """

            return np.isnan(y), lambda z: z.nonzero()[0]

        ya = np.asarray(y)

        yanan, yax = helper(ya)        

        ya[yanan] = np.interp(yax(yanan), yax(~yanan), ya[~yanan])
        
        return ya
        
    def fillna(self, df, maxcount=10000):        
        self.log('fillna')
        
        try:
            i = 0
            while df.isnull().values.any() and i < maxcount:
                df.fillna(method='pad', limit=i, inplace=True) # fill NaN's forward, 1 by 1
                df.fillna(method='bfill', limit=i, inplace=True) # fill NaN's backward, 1 by 1
                i = i + 1
                
            df.drop_duplicates(inplace=True)
        except:
            pass
        
        return df

    def constantdeltat(self, df, deltat='40000U'):        
        self.log('constantdeltat')
        
        df = df.resample(deltat).mean() # constant delta t
                
        df = self.fillna(df)     

        return df

    def alert(self, timestamp, msg):
        print('**********')
        print(str(timestamp) + ': ' + msg)
        print('**********')

    def get_field_range(self, rows, field):
        self.log('get_field_range')
        
        earlyfield = 0
        recentfield = 0
        mintime = 0
        maxtime = 0
        for i, row in rows.iterrows():
            if float(row['relative_timestamp']) <= mintime:
                earlyfield = float(row[field])
                mintime = float(row['relative_timestamp'])
            if float(row['relative_timestamp']) >= maxtime:
                recentfield = float(row[field])
                maxtime = float(row['relative_timestamp'])

        return earlyfield, recentfield

    def get_time_range(self, rows):
        self.log('get_time_range')
        
        maxtime = 0
        mintime = 0
        for i, row in rows.iterrows():
            if float(row['relative_timestamp']) <= mintime:
                mintime = float(row['relative_timestamp'])
            if float(row['relative_timestamp']) >= maxtime:
                maxtime = float(row['relative_timestamp'])

        return mintime, maxtime

    # valdict should include the index column and value as this is the row searched by the update in the main dataframe
    def update_fields(self, df, valdict, indexcol):        
        self.log('update_fields')
        
        newdf = pd.DataFrame(valdict)
        newdf.set_index(indexcol, inplace=True)
        df.update(newdf)
        
    # append columns to the data
    def augment(self, body):
        self.log('augment')
        
        prxwnd = []
        
        # these aggregates prefer some data in the body - not just one row, or else the means will always be reported as 0
        rssis = dict()
        for row in body['data']:
            freeformjson = row['freeform']
            freeform = json.loads(freeformjson, parse_int=False, parse_float=False)
            
            while not (type(freeform) is dict):
                freeform = json.loads(freeform, parse_int=False, parse_float=False)
            
            for col in freeform:
                row[col] = str(freeform[col])
                
            # compute true doppler in Hz from doppler by converting from two's complement and dividing by 16 to get the 4 fractional bits on the right
            raw_doppler = int(row['doppler'])
            if raw_doppler > 32767:
                raw_doppler = raw_doppler - 65536
            else:
                raw_doppler = raw_doppler
            raw_doppler = raw_doppler * 1.0 / 16
            row['doppler_hz'] = raw_doppler

            #print row['doppler_hz'], row['doppler_by_phase']

            # compute estimated rssi for each data point and the mean for each channel burst
            self.rssi_estimator.add_data(float(row['rssi']), int(row['relative_timestamp']))
            estimated_rssi, measured_rssi = self.rssi_estimator.get_current_rssi()
            row['estimated_rssi'] = estimated_rssi

            if not (str(row['channelindex']) + '|' + str(row['antenna']) + '|' + str(row['epc96'])) in rssis:
                rssis[(str(row['channelindex']) + '|' + str(row['antenna']) + '|' + str(row['epc96']))] = []
            rssis[(str(row['channelindex']) + '|' + str(row['antenna']) + '|' + str(row['epc96']))].append(float(row['estimated_rssi']))

        prevrow = None
        prevreads = dict()
        
        for row in body['data']:
            # rssi from mean, doppler by channel, and phase to radians
            rssi_from_mean = float(row['estimated_rssi']) - np.mean(rssis[(str(row['channelindex']) + '|' + str(row['antenna']) + '|' + str(row['epc96']))])
            rssi_from_min = float(row['estimated_rssi']) - min(rssis[(str(row['channelindex']) + '|' + str(row['antenna']) + '|' + str(row['epc96']))])
            doppler_channel = doppler_by_channel(float(row['doppler_hz']), int(row['channelindex']))
            phase_rads = phase_to_rads(float(row['phase']))

            row['rssi_from_mean'] = rssi_from_mean
            row['rssi_from_min'] = rssi_from_min
            row['doppler_channel'] = doppler_channel
            row['phase_rads'] = phase_rads
            row['phase_cos_rads'] = math.cos(phase_rads)
            
            # Solve for moving_parts == gtag**2 * R (the return loss) / r**4 (the radius)
            prxLinear = 10**(float(row['rssi']) * 0.1) * 1000 # convert to Watts from dbm
            ptx = 1 # 1W = 30 dbm power from transmitter
            gr = 9 #reader gain (constant) - gain is 4 pi Aperature / lambda**2, so this really assumes a constant aperature; the lambda**2 component cancels out with gtag on the other side, since the frequency used is the same
            wavelength = (cspeed * 1.0 / freqbychannel(int(row['channelindex']))) # lambda
            #prx_moving_parts = ((1.0/prxLinear) * (4 * math.pi)**4) * 1.0 / (ptx * gr**2 * wavelength**4)
            prx_moving_parts = (ptx * gr**2) * 1.0 / (prxLinear * (wavelength**4)) # using aperature instead of gain for gt and gr terms, with the aperature formula integrated into prx_moving_parts
            row['prx_moving_parts'] = 10 * np.log10(prx_moving_parts * 1.0 / 1000)
            
            xi = 0.00961892564782412 # was 0.009405417 for gain only and not aperature
            prxval = float(row['prx_moving_parts']) + (xi * (50-int(row['channelindex'])))
            row['prx_moving_parts_deoscillated'] = prxval
            
            prxwnd.append(prxval)
            
            #next 4 lines ADDED by Rob 10-18-17
            # compute estimated_prx_moving_parts_deoscillated for each data point
            self.prx_m_p_d_estimator.add_data(float(row['prx_moving_parts_deoscillated']), int(row['relative_timestamp']))
            estimated_prx_m_p_d, measured_prx_m_p_d = self.prx_m_p_d_estimator.get_current_rssi()
            row['estimated_prx_m_p_d'] = estimated_prx_m_p_d

            # velocity from doppler shift
            velocity_by_doppler = float(row['doppler_hz']) * cspeed * 1.0 / freqbychannel(int(row['channelindex']))
            row['velocity_by_doppler'] = velocity_by_doppler

            # velocity from phase difference, assuming the channel, antenna, and epc96 are the same from the previous row; can also use to compute doppler frequency from phase
            # CBID paper
            if not (prevrow is None) and prevrow['channelindex'] == row['channelindex'] and prevrow['antenna'] == row['antenna'] and prevrow['epc96'] == row['epc96']:
                if not ((4 * (1/self.timescale) * (float(row['relative_timestamp']) - float(prevrow['relative_timestamp'])) * math.pi) == 0):
                    deltaphase = (float(row['phase_rads']) - float(prevrow['phase_rads']))
                    if deltaphase >= 2 * math.pi:
                        deltaphase = deltaphase - 2 * math.pi
                    if deltaphase < -1 * math.pi:
                        deltaphase = deltaphase + 2 * math.pi
                    velocity_by_phase = (cspeed * 1.0 / freqbychannel(int(row['channelindex']))) * deltaphase * 1.0 / (4 * (1/self.timescale) * (float(row['relative_timestamp']) - float(prevrow['relative_timestamp'])) * math.pi)
                else:
                    velocity_by_phase = np.nan

                doppler_by_phase = velocity_by_phase * freqbychannel(int(row['channelindex'])) * 1.0 / cspeed
            elif str(row['channelindex'] + '|' + row['antenna'] + '|' + row['epc96']) in prevreads:
                if not ((4 * (1/self.timescale) * (float(row['relative_timestamp']) - float(prevreads[row['channelindex'] + '|' + row['antenna'] + '|' +  row['epc96']]['relative_timestamp'])) * math.pi) == 0):
                    deltaphase = (float(row['phase_rads']) - float(prevreads[row['channelindex'] + '|' + row['antenna'] + '|' + row['epc96']]['phase_rads']))
                    if deltaphase >= 2 * math.pi:
                        deltaphase = deltaphase - 2 * math.pi
                    if deltaphase < -1 * math.pi:
                        deltaphase = deltaphase + 2 * math.pi
                    velocity_by_phase = (cspeed * 1.0 / freqbychannel(int(row['channelindex']))) * deltaphase * 1.0 / (4 * (1/self.timescale) * (float(row['relative_timestamp']) - float(prevreads[row['channelindex'] + '|' + row['antenna'] + '|' + row['epc96']]['relative_timestamp'])) * math.pi)
                else:
                    velocity_by_phase = np.nan

                doppler_by_phase = velocity_by_phase * freqbychannel(int(row['channelindex'])) * 1.0 / cspeed
            else:
                velocity_by_phase = np.nan
                doppler_by_phase = np.nan

            row['doppler_by_phase'] = doppler_by_phase
            row['velocity_by_phase'] = velocity_by_phase
            
            if not (prevrow is None) and prevrow['channelindex'] == row['channelindex'] and prevrow['antenna'] == row['antenna'] and prevrow['epc96'] == row['epc96']:
                rssi_delta = float(row['rssi']) - float(prevrow['rssi'])
                row['rssi_delta'] = rssi_delta
            
            prevrow = row
            prevreads[str(row['channelindex'] + '|' + row['antenna'] + '|' + row['epc96'])] = row

        return body

    def setcolumn(self, df, col, coltype):        
        self.log('setcolumn')
        
        if col not in df:
            df[col] = np.nan
        df[col] = df[col].astype(coltype)
                
        return df

    def append_data(self, df, body):        
        self.log('append_data')
        
        bodydf = pd.DataFrame(body['data'])
        dfs = [df, bodydf]
        
        #self.log(dfs)
        #self.log(bodydf)
        #self.log(len(body['data']))
        
        df = pd.concat(dfs)
                
        return df
        
    def add_data(self, body, filterfield=None, filtervalue=None):
        self.log('add_data')
        
        if not 'data' in body:
            return

        if len(body['data']) == 0:
            return

        body = self.augment(body)
        
        self.log('appending augmented body')        
        self.df = self.append_data(self.df, body)
        self.log('setting time delta index')
        self.df['timedeltaindex'] = pd.to_timedelta(self.df['relative_timestamp'], unit='us')
        self.log('setting index')
        self.df.set_index('timedeltaindex', inplace=True)
        self.log('sorting')
        self.df.sort_values(by='relative_timestamp', inplace=True)
        self.log('setting last max timestamp')
        last_max_relative_timestamp = self.max_relative_timestamp
        self.max_relative_timestamp = self.df['relative_timestamp'].max()
        
        if not (filterfield is None) and not (filtervalue is None):
            self.df.drop(self.df[self.df[filterfield] != filtervalue].index, inplace = True)        

        self.df = self.setcolumn(self.df, 'antenna', float)
        self.df = self.setcolumn(self.df, 'channelindex', float)
        self.df = self.setcolumn(self.df, 'rssi', int)
        self.df = self.setcolumn(self.df, 'epc96', str)
        self.df = self.setcolumn(self.df, 'velocity_by_phase', float)
        self.df = self.setcolumn(self.df, 'rssi_delta', float)
        self.df = self.setcolumn(self.df, 'rssi_from_mean', float)
        self.df = self.setcolumn(self.df, 'rssi_from_min', float)
        self.df = self.setcolumn(self.df, 'doppler_channel', float)
        self.df = self.setcolumn(self.df, 'phase_rads', float)     
        self.df = self.setcolumn(self.df, 'doppler_by_phase', float)
        self.df = self.setcolumn(self.df, 'velocity_by_doppler', float)
        self.df = self.setcolumn(self.df, 'doppler_hz', float)
        self.df = self.setcolumn(self.df, 'estimated_rssi', float)
        self.df = self.setcolumn(self.df, 'prx_moving_parts', float)
        self.df = self.setcolumn(self.df, 'prx_moving_parts_deoscillated', float)
        self.df = self.setcolumn(self.df, 'phase_cos_rads', float) 
        self.df = self.setcolumn(self.df, 'estimated_prx_m_p_d', float)#ADDED by Rob 10-18-17       

        self.df = self.fillna(self.df)
        
    # this is the method that you will override, but should include the method above
    def start(self, body, filterfield=None, filtervalue=None):
        self.add_data(body, filterfield, filtervalue)
