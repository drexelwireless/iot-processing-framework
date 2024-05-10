import sys
import getopt
import json
import time
import threading
from graph_animator import GraphAnimator
import os
import operator
import datetime
import math
import numpy as np
import requests

cspeed = 2.99792458e8

# http://www.ptsmobile.com/impinj/impinj-speedway-user-guide.pdf
def freqbychannel(ch):
    if ch < 1 or ch > 50:
        return -1
    else:
        return 1e6 * (902.75 + 0.5 * (ch-1)) # 902-928 MHz, 50 channels of 500 kHz each

# Defaults:
server = 'https://localhost:5000'
db_password = 'abc123'
do_debug = False
certfile = 'NONE'
simulate_real_time = False
timescale = int(1e6)
moviefile = None
taglist = None

def log(msg):
    global do_debug

    if do_debug:
        print(msg)

def sendhttp(url, headerdict=dict(), bodydict=dict(), method='POST'):
    global certfile

    if certfile == 'NONE':
        verifypath = False
    else:
        verifypath = certfile

    if method.lower() == 'get':
        fun = requests.get
    elif method.lower() == 'put':
        fun = requests.put
    elif method.lower() == 'post':
        fun = requests.post

    response = fun(url, verify = verifypath, data = json.dumps(bodydict), headers=headerdict)

    return response, response.text
    
def retrieve_since(timestamp):
    global db_password
    global server

    resp, content = sendhttp(server + '/api/iot/' + str(timestamp), headerdict={'Content-Type': 'application/json'}, bodydict={'data': {'db_password': db_password}}, method='POST')

    return resp, content
    
def retrieve_last_n_data(n=1):
    global db_password
    global server

    resp, content = sendhttp(server + '/api/iot/seconds/' + str(n), headerdict={'Content-Type': 'application/json'}, bodydict={'data': {'db_password': db_password}}, method='POST')

    return resp, content

def retrieve_data(start, end):
    global timescale
    global db_password
    global server

    resp, content = sendhttp(server + '/api/iot/' + str(start * timescale) + '/' + str(end * timescale), headerdict={'Content-Type': 'application/json'}, bodydict={'data': {'db_password': db_password}}, method='POST')

    return resp, content

def get_max_reltime():
    global server

    resp, content = sendhttp(server + '/api/iot/maxtime', method='GET')

    return resp, content

############################################## OPTIONS
def usage(server, db_password, certfile, timescale, simulate_real_time, moviefile, do_debug):
	print('%s [<options>]' % sys.argv[0])
	print('where <options> are:\n' \
			'\t-h - show this help message\n' \
			'\t-o <host> - host web service to retrieve data: default %s\n' \
            '\t-p <password> - database password: default %s\n' \
            '\t-c <certfile> - path to the certificate file for verifying SSL certificate or NONE to bypass: default %s\n' \
            '\t-t <timescale> - scale of interrogator time (i.e., 1 for 1 unit per second): default %s\n' \
            '\t-i - simulate real-time by going through the whole database contents from the beginning, instead of pulling from the end: default %s\n' \
            '\t-m <moviefile> - optionally output to a video file\n' \
			'\t-d - Enable debugging: default %s\n' \
            '\t-f <tag,tag> - filter by comma separated list of tags to show (default: show all tags)\n' % (server, db_password, certfile, timescale, simulate_real_time, do_debug))
	sys.exit(1)

def getopts():
    global server
    global db_password
    global certfile
    global timescale
    global simulate_real_time
    global do_debug
    global moviefile
    global taglist

	# Check command line
    optlist, list = getopt.getopt(sys.argv[1:], 'ho:p:c:t:dim:f:')
    for opt in optlist:
        if opt[0] == '-h':
            usage(server, db_password, certfile, timescale, simulate_real_time, moviefile, do_debug)
        if opt[0] == '-p':
            db_password = opt[1]
        if opt[0] == '-o':
            server = opt[1]
        if opt[0] == '-c':
            certfile = opt[1]
        if opt[0] == '-t':
            timescale = int(opt[1])
        if opt[0] == '-i':
            simulate_real_time = True
        if opt[0] == '-d':
            do_debug = True
        if opt[0] == '-m':
            moviefile = opt[1]
        if opt[0] == '-f':
            if ',' in opt[1]:
                taglist = opt[1].split(',')
            else:
                taglist = []
                taglist.append(opt[1])

    return server, db_password, certfile, timescale, simulate_real_time, moviefile, do_debug, taglist

############################################## MAIN AND HELPERS
# Function to watch CTRL+C keyboard input
def prog_quit(QUITFILE='quit'):
    print("Create file " + QUITFILE + " to quit.")
    while 1:
        try:
            if os.path.isfile(QUITFILE):
                print(QUITFILE + " has been found")
                os._exit(0)
            time.sleep(1)
        except:
            os._exit(0)

# graph, animate, and interpolate given a list of tags sorted by increasing timestamp, and the name and units (for labeling) of the xfield and yfield to plot / inerpolate.  Assumes that xfield is the timestamp field.  Also given is the polynomial order to fit, and the interpolation step value over the x axis.  Also give the extrapolate factor.  Also optionally give an mp4 filename to export.  Also give a time in microseconds to view.  Also optionally give whether to dynamically update y axis range based on data range.
# Separate plots for each signature
def animate(tag_array):
	global moviefile

	ganim = GraphAnimator(tag_array, xfield='relative_timestamp', yfield='rssi', unitx='time', unity='Prx dBm', time=60000000, dynamic_y_axis=True, keyfield='epc96|antenna', xtime=5000000, invert_y=False, interval=10)
	ganim.animate(moviefile)

def add_tags_to_tagarray(body, ta):
    lst = []
    
    if not (taglist is None) and len(taglist) > 0:
        include = False
        for entry in body['data']:
            for tag in taglist:
                if entry['epc96'] == tag:
                    include = True
                    break
                
            if include:
                lst.append(entry)
    else:
        lst = body['data']
    
    ta.extend(lst)
    #for entry in lst:
        #print entry
        #ta.append(entry)         

def aggregate_by_channel(body):    
    for row in body['data']:
        freeform = json.loads(row['freeform'], parse_int=False, parse_float=False)
            
        while not (type(freeform) is dict):
            freeform = json.loads(freeform, parse_int=False, parse_float=False)
            
        for col in freeform:
            row[col] = str(freeform[col])
        
        # Solve for moving_parts == gtag**2 * R (the return loss) / r**4 (the radius)
        prxLinear = 10**(float(row['rssi']) * 0.1) * 1.0 / 1000 # convert to Watts from dbm
        ptx = 1 # 1W = 30 dbm power from transmitter
        gr = 6 #reader gain (constant)
        wavelength = (cspeed * 1.0 / freqbychannel(int(row['channelindex'])))
        prx_moving_parts = (prxLinear * (4 * math.pi)**4) * 1.0 / (ptx * gr**2 * wavelength**4)
        row['rssi'] = 10 * np.log10(prx_moving_parts * 1000)
 
    return body

def get_max_time_in_body(body):
    maxtime = 0
    for row in body['data']:
        if int(row['relative_timestamp']) > maxtime:
            maxtime = int(row['relative_timestamp'])

    return maxtime
    
def readdata(ta):
    global timescale

    # if simulating real time, figure out how long the database goes
    if simulate_real_time == True:
        resp, content = get_max_reltime()
        body = json.loads(content)
        #print body
        max_db_time = int(body['data'][0]['max_relative_timestamp'])
    else:
        max_db_time = -1

    iterations = 0

    prevread = None
    seconds = 1
    lastreltime = -1
    while 1:
        if not (prevread is None):
            while (datetime.datetime.now() - prevread).total_seconds() < seconds:
                time.sleep(0.025)
                
        # get data
        if simulate_real_time == True:
            resp, content = retrieve_data(iterations, iterations+seconds)
        else:
            if lastreltime == -1:
                resp, content = retrieve_last_n_data(n=seconds)
            else:
                resp, content = retrieve_since(lastreltime)
        
        prevread = datetime.datetime.now()

        try:
            body = json.loads(content)
        except:
            continue
            
        lastreltime = get_max_time_in_body(body)

        #print body
        #for entry in body['data']:
        #    print entry['relative_timestamp']

        if simulate_real_time == True and (iterations * timescale) > max_db_time:
            break

        # process
        body = aggregate_by_channel(body)
        add_tags_to_tagarray(body, ta)

        # advance
        iterations = iterations + seconds

def run():
    ta = []

    t1 = threading.Thread(target = readdata, args=(ta, ))
    t1.start()

    t2 = threading.Thread(target = prog_quit, args=())
    t2.start()

    animate(ta)

if __name__ == '__main__':
    getopts()

    run()
