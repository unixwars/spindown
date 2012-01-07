#!/usr/bin/env python

# Spindown every /sys/block/sd* device after specified idle time
# Needs package sdparm and root privileges

# (C) 2009, Taher Shihadeh <taher@unixwars.com>
# Licensed: GPL v2

import getopt
import time
import sys
import os

DISKPATH = '/sys/block/'
SLEEPVAL = 60  # 1 minute
INTERVAL = 300 # 5 minute
CMDTMPLT = 'sdparm --flexible --command=%s /dev/%s &>/dev/null'


def help():
  help="""Usage: spindown [-h] | [[-i seconds] | [-s] | [-e sda [-e sdb ...]]]

Parameters:
  -h, --help      this help screen
  -e, --exclude   do not operate on specified drive
  -i, --interval  idle seconds above which the drives should spin down
  -s, --simulate  do not perform actions, just simulate what would happen
"""
  print help


def parse_args(params):
    try:
        opts, args = getopt.getopt(params, "hi:e:s",
                                   ["help", "interval=", "exclude=", "simulate"])
    except getopt.GetoptError:
        help()
        sys.exit(1)

    params = {
        'simulate' : False,
        'interval' : INTERVAL,
        'sleepval' : SLEEPVAL,
        'exclude'  : []
        }

    for o, a in opts:
        if o in ("-h", "--help"):
            help()
            sys.exit(1)
        if o in ("-i", "--interval"):
            try:
                a = int(a)
                params['interval'] = a
            except ValueError:
                help()
                sys.exit(1)
        if o in ("-s", "--simulate"):
            params['simulate'] = True
        if o in ("-e", "--exclude"):
            params['exclude'].append(a)

    if params['interval'] < SLEEPVAL:
        params['sleepval'] = params['interval'] / 2

    return params


def main(params):
    info = {}
    # see what drives need monitoring
    drives = os.listdir(DISKPATH)
    drives = filter (lambda x: len(x) == 3 and x[:2] == 'sd', drives)
    drives = filter (lambda x: x not in params['exclude'], drives)

    if len(drives) == 0:
        print 'Nothing to do.',
        return

    for drive in drives:
        info[drive] = {'stat': '', 'time': 0, 'spin': True}

    while True:
        for drive in drives:
            the_stat = open(DISKPATH + drive + '/stat').read()
            the_time = time.time()

            # If status has not changed
            if info[drive]['stat'] == the_stat:
                if the_time - info[drive]['time'] >= params['interval'] and \
                   info[drive]['spin'] == True:

                    cmd = CMDTMPLT % ('sync', drive) + ' ; ' + \
                          CMDTMPLT % ('stop', drive)

                    if params['simulate']:
                        print 'Simulation: no %s activity in the last ' \
                              '%s seconds.\n' % (drive,params['interval'])
                    else:
                        ret = os.system (cmd)
                        if ret != 0:
                            sys.exit('Could nos stop %s' % drive)
            else:
                info[drive] = {'stat' : the_stat,
                               'time' : the_time,
                               'spin' : True}
        time.sleep(params['sleepval'])


if __name__ == "__main__":
    try:
        params = parse_args(sys.argv[1:])
        main(params)
    except KeyboardInterrupt:
        print "Keyboard interrupt. ",
    print "Terminating process."

