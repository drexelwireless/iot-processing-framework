import sys
import getopt
import requests
import json
import time
import threading
import os
import operator
import datetime
import importlib 
sys.path.insert(0, os.getcwd()) # import from current directory

# Defaults:
server = 'https://localhost:5000'
db_password = 'abc123'
do_debug = False
certfile = 'NONE'
timescale = int(1e6)
sensor = ''

############################################## OPTIONS
def usage(server, db_password, certfile, timescale, do_debug):
	print('%s [<options>] [<sensor>]' % sys.argv[0])
	print('where <options> are:\n' \
			'\t-h - show this help message\n' \
			'\t-o <host> - host web service to retrieve data: default %s\n' \
            '\t-p <password> - database password: default %s\n' \
            '\t-c <certfile> - path to the certificate file for verifying SSL certificate or NONE to bypass: default %s\n' \
            '\t-t <timescale> - scale of interrogator time (i.e., 1 for 1 unit per second): default %s\n' \
            '\tsensor is any module and class included in the current directory, i.e., sensor_respiratoryrate.RespiratoryRateSensor\n' \
			'\t-d - Enable debugging: default %s\n' % (server, db_password, certfile, timescale, do_debug))
	sys.exit(1)

def getopts():
    global server
    global db_password
    global certfile
    global timescale
    global do_debug
    global sensor

	# Check command line
    optlist, argslist = getopt.getopt(sys.argv[1:], 'ho:p:c:t:dim:s:')
    
    # if no processors specified, quit
    if len(argslist) == 0:
        print('Must specify one sensor.')
        usage(server, db_password, certfile, timescale, do_debug)
        sys.exit(1)
    
    for opt in optlist:
        if opt[0] == '-h':
            usage(server, db_password, certfile, timescale, do_debug)
        if opt[0] == '-p':
            db_password = opt[1]
        if opt[0] == '-o':
            server = opt[1]
        if opt[0] == '-c':
            certfile = opt[1]
        if opt[0] == '-t':
            timescale = int(opt[1])
        if opt[0] == '-d':
            do_debug = True
            
    sensor = argslist[0]

    return server, db_password, certfile, timescale, do_debug
 
############################################## MAIN AND HELPERS   
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

def retrieve_last_n_data(n=1):
    global db_password
    global server

    resp, content = sendhttp(server + '/api/iot/stats/seconds/' + str(n), headerdict={'Content-Type': 'application/json'}, bodydict={'data': {'db_password': db_password}}, method='POST')

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
   
def readdata():
    global timescale
    global sensor

    # find out how long the database goes
    resp, content = get_max_reltime()
    body = json.loads(content)
    #print body
    max_db_time = int(body['data'][0]['max_relative_timestamp'])

    # get all data
    resp, content = retrieve_data(0, int(max_db_time * 1.0 / timescale))

    body = json.loads(content)
    
    # for the sensor, determine what it is, pass it all the data and launch
    ptclass = getattr(importlib.import_module(sensor.split(".")[0]), sensor.split(".")[1])
    ptinstance = ptclass() # instantiate the Processor subobject
    ptinstance.start(body)
    
def run():    
    t1 = threading.Thread(target = prog_quit, args=())
    t1.start()
    
    readdata()
    os._exit(0)
    
if __name__ == '__main__':
    getopts()

    run()
