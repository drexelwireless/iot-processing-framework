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
from plotter import *
sys.path.insert(0, os.getcwd()) # import from current directory

# Defaults:
server = 'https://localhost:5000'
db_password = 'abc123'
do_debug = False
certfile = 'NONE'
simulate_real_time = False
timescale = int(1e6)
processors = []
processor_threads = []
savemovie = False
moviefile = 'out.mp4'

############################################## OPTIONS
def usage(server, db_password, certfile, timescale, simulate_real_time, savemovie, moviefile, do_debug):
	print('%s [<options>] [<processor1> <processor2> ...]' % sys.argv[0])
	print('where <options> are:\n' \
			'\t-h - show this help message\n' \
			'\t-o <host> - host web service to retrieve data: default %s\n' \
            '\t-p <password> - database password: default %s\n' \
            '\t-c <certfile> - path to the certificate file for verifying SSL certificate or NONE to bypass: default %s\n' \
            '\t-t <timescale> - scale of interrogator time (i.e., 1 for 1 unit per second): default %s\n' \
            '\t-i - simulate real-time by going through the whole database contents from the beginning, instead of pulling from the end: default %s\n' \
            '\t-s <moviefilename> - save the movie plot with the given pathname: default %s with a path of %s\n' \
            '\tprocessors include any module and class included in the current directory, i.e., processor_respiratoryrate.RespiratoryRateProcessor\n' \
			'\t-d - Enable debugging: default %s\n' % (server, db_password, certfile, timescale, simulate_real_time, savemovie, moviefile, do_debug))
	sys.exit(1)

def getopts():
    global server
    global db_password
    global certfile
    global timescale
    global simulate_real_time
    global do_debug
    global processors
    global savemovie
    global moviefile

	# Check command line
    optlist, argslist = getopt.getopt(sys.argv[1:], 'ho:p:c:t:dim:s:')
    
    # if no processors specified, quit
    if len(argslist) == 0:
        print('Must specify at least one processor.')
        usage(server, db_password, certfile, timescale, simulate_real_time, savemovie, moviefile, do_debug)
        sys.exit(1)
    
    for opt in optlist:
        if opt[0] == '-h':
            usage(server, db_password, certfile, timescale, simulate_real_time, savemovie, moviefile, do_debug)
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
        if opt[0] == '-s':
            savemovie = True
            moviefile = opt[1]
            
    processors.extend(argslist)

    return server, db_password, certfile, timescale, simulate_real_time, processors, savemovie, moviefile, do_debug
 
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
    
def add_data_to_processor_thread(pt, body):
    pt.add_data(body)
   
def readdata(pt_sem):
    global timescale
    global processors
    global processor_threads
    
    for processor in processors:
        # for each processor, determine what it is, and start the appropriate subobject thread, passing it data as it comes, add to the threads list, and start
        ptclass = getattr(importlib.import_module(processor.split(".")[0]), processor.split(".")[1])
        ptinstance = ptclass() # instantiate the Processor subobject
        processor_threads.append(ptinstance)
        ptinstance.start_thread()
    pt_sem.release()

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
    while 1:
        # get data
        if simulate_real_time == True:
            resp, content = retrieve_data(iterations, iterations+seconds)
        else:
            resp, content = retrieve_last_n_data(n=seconds)

        if not (prevread is None):
            #print "delay since last read:", (datetime.datetime.now() - prevread).total_seconds()
            while (datetime.datetime.now() - prevread).total_seconds() < seconds:
                time.sleep(0.025)
        
        prevread = datetime.datetime.now()

        body = json.loads(content)
        #print body
        #for entry in body['data']:
        #    print entry['relative_timestamp']
        
        add_data_threads = [] 
        for pt in processor_threads:
            t = threading.Thread(target=add_data_to_processor_thread, args=(pt, body, ))
            add_data_threads.append(t)
            t.start()

        for t in add_data_threads:
            t.join()

        if simulate_real_time == True and (iterations * timescale) > max_db_time:
            break

        # advance
        iterations = iterations + seconds
        
    # notify the threads that we are done
    for pt in processor_threads:
        pt.notify_finished()
    
    # wait for the processors to finish    
    for pt in processor_threads:
        pt.join_thread()

def run():
    global processor_threads
    global savemovie
    global moviefile
    
    pt_sem = threading.Semaphore(0)
    
    t1 = threading.Thread(target = prog_quit, args=())
    t1.start()
    
    t2 = threading.Thread(target = readdata, args=(pt_sem,))
    t2.start()
    
    pt_sem.acquire() # wait until all processor threads have started

    plotter = Plotter(processor_threads)
    plotter.start(save=savemovie, moviefilename=moviefile)
    
if __name__ == '__main__':
    getopts()

    run()
