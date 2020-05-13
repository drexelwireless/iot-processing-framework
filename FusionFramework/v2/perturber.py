import threading
import pandas as pd
import numpy as np
import math
import filterpy.kalman as kf

class Perturber(object):
    def __init__(self):
        pass
        
    def perturb(self, body):
        pass
        
    def doppler_raw2hz(self, raw_doppler):
        doppler = raw_doppler
        
        if raw_doppler > 32767:
            doppler = raw_doppler - 65536
        doppler = doppler * 1.0 / 16
        
        return doppler
    
    def doppler_hz2raw(self, doppler_hz):
        doppler = doppler_hz * 16
        if doppler < 0:
            doppler = doppler + 65536
            
        return doppler        
