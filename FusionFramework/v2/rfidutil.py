import math
import scipy.stats
import numpy as np

cspeed = 2.99792458e8

def ttest(sample, trainmean, trainvar, trainlen):
    t = (sample - trainmean) * 1.0 / ((math.sqrt(trainvar) * 1.0) / trainlen)
    p = 1-scipy.stats.t.sf(t, trainlen-1)
    
    #print 'sample', sample, 'mean', trainmean, 'var', trainvar, 'len', trainlen, 'p', p
        
    return t,p
        
# http://www.ptsmobile.com/impinj/impinj-speedway-user-guide.pdf
def freqbychannel(ch):
    if ch < 1 or ch > 50:
        return -1
    else:
        return 1e6 * (902.75 + 0.5 * (ch-1)) # 902-928 MHz, 50 channels of 500 kHz each
							
def doppler_by_channel(doppler, ch):
    return doppler * freqbychannel(ch)

def phase_to_rads(phase):
    return phase * 2.0 * math.pi / 4096
    
# https://gist.github.com/endolith/250860
def peakdet(v, delta, x = None):
    from numpy import NaN, Inf, arange, isscalar, asarray, array
    import sys
    """
    Converted from MATLAB script at http://billauer.co.il/peakdet.html

    Returns two arrays

    function [maxtab, mintab]=peakdet(v, delta, x)
    %PEAKDET Detect peaks in a vector
    %        [MAXTAB, MINTAB] = PEAKDET(V, DELTA) finds the local
    %        maxima and minima ("peaks") in the vector V.
    %        MAXTAB and MINTAB consists of two columns. Column 1
    %        contains indices in V, and column 2 the found values.
    %      
    %        With [MAXTAB, MINTAB] = PEAKDET(V, DELTA, X) the indices
    %        in MAXTAB and MINTAB are replaced with the corresponding
    %        X-values.
    %
    %        A point is considered a maximum peak if it has the maximal
    %        value, and was preceded (to the left) by a value lower by
    %        DELTA.

    % Eli Billauer, 3.4.05 (Explicitly not copyrighted).
    % This function is released to the public domain; Any use is allowed.
    """
    maxtab = []
    mintab = []
   
    if x is None:
        x = arange(len(v))

    v = asarray(v)

    if len(v) != len(x):
        sys.exit('Input vectors v and x must have same length')

    if not isscalar(delta):
        sys.exit('Input argument delta must be a scalar')

    if delta <= 0:
        #print 'Input argument delta must be positive'
        return [],[]
    mn, mx = Inf, -Inf
    mnpos, mxpos = NaN, NaN

    lookformax = True

    for i in arange(len(v)):
        this = v[i]
        if this > mx:
            mx = this
            mxpos = x[i]
        if this < mn:
            mn = this
            mnpos = x[i]
    
        if lookformax:
            if this < mx-delta:
                maxtab.append((mxpos, mx))
                mn = this
                mnpos = x[i]
                lookformax = False
        else:
            if this > mn+delta:
                mintab.append((mnpos, mn))
                mx = this
                mxpos = x[i]
                lookformax = True
    
    return array(maxtab), array(mintab)

def peakdet2(v, delta, x = None):
    from numpy import NaN, Inf, arange, isscalar, asarray, array
    import sys
    """
    Converted from MATLAB script at http://billauer.co.il/peakdet.html

    Returns two arrays

    function [maxtab, mintab]=peakdet(v, delta, x)
    %PEAKDET Detect peaks in a vector
    %        [MAXTAB, MINTAB] = PEAKDET(V, DELTA) finds the local
    %        maxima and minima ("peaks") in the vector V.
    %        MAXTAB and MINTAB consists of two columns. Column 1
    %        contains indices in V, and column 2 the found values.
    %      
    %        With [MAXTAB, MINTAB] = PEAKDET(V, DELTA, X) the indices
    %        in MAXTAB and MINTAB are replaced with the corresponding
    %        X-values.
    %
    %        A point is considered a maximum peak if it has the maximal
    %        value, and was preceded (to the left) by a value lower by
    %        DELTA.

    % Eli Billauer, 3.4.05 (Explicitly not copyrighted).
    % This function is released to the public domain; Any use is allowed.

    Note: Rob added the code block near the end of the algorithm to eliminate 
    initial and/or final extrema, if they are within delta of the initial and/or final
    points in the window.  In this way, the "greater than delta away" constraint is applied
    to the initial and final extrema as well.
    """
    maxtab = []
    mintab = []
   
    if x is None:
        x = arange(len(v))

    v = asarray(v)

    if len(v) != len(x):
        sys.exit('Input vectors v and x must have same length')

    if not isscalar(delta):
        sys.exit('Input argument delta must be a scalar')

    if delta <= 0:
        #print 'Input argument delta must be positive'
        return [],[]
    mn, mx = Inf, -Inf
    mnpos, mxpos = NaN, NaN

    lookformax = True

    for i in arange(len(v)):
        this = v[i]
        if this > mx:
            mx = this
            mxpos = x[i]
        if this < mn:
            mn = this
            mnpos = x[i]
    
        if lookformax:
            if this < mx-delta:
                maxtab.append((mxpos, mx))
                mn = this
                mnpos = x[i]
                lookformax = False
        else:
            if this > mn+delta:
                mintab.append((mnpos, mn))
                mx = this
                mxpos = x[i]
                lookformax = True

    return array(maxtab), array(mintab)
    
# http://stackoverflow.com/questions/22583391/peak-signal-detection-in-realtime-timeseries-data   
def peaks(y, lag=5, threshold=3, influence=0.5, buffer=0.5):
    if len(y) <= lag+1:
        return [], [], []
        
    signals = [0] * len(y)
    filteredY = [0] * len(y)
    for i in range(lag):
        filteredY[i] = y[i]
    avgFilter = [0] * len(y)
    stdFilter = [0] * len(y)
    avgFilter[lag] = np.mean(filteredY)
    stdFilter[lag] = np.std(filteredY)
    
    lowthresholds = [0] * len(y)
    highthresholds = [0] * len(y)
    
    for i in range(lag+1, len(y)):
        lowthresholds[i] = avgFilter[i-1] - (threshold * stdFilter[i-1]) - buffer
        highthresholds[i] = avgFilter[i-1] + (threshold * stdFilter[i-1]) + buffer
        
        #print y[i], avgFilter[i-1], lowthresholds[i], highthresholds[i]
        
        if y[i] > highthresholds[i]:
            signals[i] = 1
        elif y[i] < lowthresholds[i]:
            signals[i] = -1
        else:
            signals[i] = 0

        filteredY[i] = (influence * y[i]) + ((1-influence) * filteredY[i-1])
        avgFilter[i] = np.mean(filteredY[i-lag:i])
        stdFilter[i] = np.std(filteredY[i-lag:i])
    
    return signals, lowthresholds, highthresholds
    
def rolling(data, n, fun):
    signals = []
    for i in range(n, len(data)):
        slice = data[i-n:i]
        signal = fun(slice)
        signals.append(signal)
    return signals
    
# direction is 'up' 'down' or 'both'
def pointcrossings(data, threshold, direction='both'):
    crossings = 0
    
    for i in range(1, len(data)):
        if data[i] > threshold and data[i-1] <= threshold:
            if direction == 'both' or direction == 'up':
                crossings = crossings + 1
                
        if data[i] <= threshold and data[i-1] > threshold:
            if direction == 'both' or direction == 'down':
                crossings = crossings + 1
                
    return crossings
    
# https://scipher.wordpress.com/2010/12/02/simple-sliding-window-iterator-in-python/
def slidingWindow(sequence,winSize,step=1):
    """Returns a generator that will iterate through
    the defined chunks of input sequence.  Input sequence
    must be iterable."""
 
    # Verify the inputs
    try: it = iter(sequence)
    except TypeError:
        raise Exception("**ERROR** sequence must be iterable.")
    if not ((type(winSize) == type(0)) and (type(step) == type(0))):
        raise Exception("**ERROR** type(winSize) and type(step) must be int.")
    if step > winSize:
        raise Exception("**ERROR** step must not be larger than winSize.")
    if winSize > len(sequence):
        raise Exception("**ERROR** winSize must not be larger than sequence length.")
 
    # Pre-compute number of chunks to emit
    numOfChunks = ((len(sequence)-winSize)/step)+1
 
    # Do the work
    for i in range(0,numOfChunks*step,step):
        yield sequence[i:i+winSize]
        
def getrollingstats(arr, wndsize, step=1):
    mns = []
    stdevs = []
    
    for wnd in slidingWindow(arr, wndsize, step=step):
        mns.append(np.mean(wnd))
        stdevs.append(np.std(wnd))
        
    return mns, stdevs    