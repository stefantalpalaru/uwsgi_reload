#!/usr/bin/env python
# vim: set fileencoding=utf-8 :

# Copyright © 2014 - Stefan Talpalaru <stefantalpalaru@yahoo.com>

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import fcntl
import time
import subprocess
import json
import argparse
from pprint import pprint


### args
parser = argparse.ArgumentParser(description='Graceful reload for uWSGI vassals.', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('--emperor-path', help='directory used by the Emperor', required=True, default=argparse.SUPPRESS, metavar='<dir>')
parser.add_argument('--fastrouter-stats-socket', help='Fastrouter statistics socket', required=True, default=argparse.SUPPRESS, metavar='<socket>')
parser.add_argument('--emperor-stats-socket', help='Emperor statistics socket', required=True, default=argparse.SUPPRESS, metavar='<socket>')
parser.add_argument('--vassal-config-file-suffix', help='vassal config file suffix', default='.ini', metavar='<string>')
parser.add_argument('--minimum-active-vassals', help='the minimum number of vassals that should be active at any given time during the reload', type=int, default=1, metavar='<int>')
parser.add_argument('--timeout', help='how long to wait for the reload of a vassal', type=int, default=60, metavar='<int>')
parser.add_argument('--check-interval', help='interval between vassal status checks (seconds)', type=float, default=0.1, metavar='<float>')
parser.add_argument('-q', '--quiet', help='supress output', action='store_true')
args = parser.parse_args()

### lock
this_file = open(__file__, 'r')
try:
    fcntl.flock(this_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
except:
    print('Unable to acquire lock. Giving up.')
    exit(1)

### vassals
def count_vassals():
    data = emperor_stats()
    return len(data['vassals'])

def get_vassals():
    data = emperor_stats()
    return data['vassals']

def get_vassal(name):
    for vassal in get_vassals():
        if vassal['id'].split('.')[0] == name:
            return vassal

def print_vassal_info(vassal_name = None):
    data = emperor_stats()
    for vassal in sorted(data['vassals'], key=lambda x: x['id']):
        name = vassal['id'].split('.')[0]
        if vassal_name is not None and vassal_name != name:
            continue
        print('\n%s:' % vassal['id'])
        print('    pid = %s' % vassal['pid'])
        print('    born = %s' % vassal['born'])
        print('    last_mod = %s' % vassal['last_mod'])
        print('    ready = %s' % vassal['ready'])
        print('    accepting = %s' % vassal['accepting'])
        print('    respawns = %s' % vassal['respawns'])
        print('    subscribed = %s' % str(is_subscribed_to_fastrouter(name)))
        break

def emperor_stats():
    out = subprocess.check_output(['uwsgi', '--connect-and-read', args.emperor_stats_socket], stderr=subprocess.STDOUT)
    return json.loads(out)

def fastrouter_stats():
    out = subprocess.check_output(['uwsgi', '--connect-and-read', args.fastrouter_stats_socket], stderr=subprocess.STDOUT)
    return json.loads(out)

def print_fastrouter_stats(name):
    data = fastrouter_stats()
    for subscription in data['subscriptions']:
        for node in subscription['nodes']:
            if node['name'].split('/')[-1].split('.')[0] == name:
                pprint(node)
                return

def print_emperor_stats(name):
    data = emperor_stats()
    for vassal in sorted(data['vassals'], key=lambda x: x['id']):
        if name == vassal['id'].split('.')[0]:
            pprint(vassal)
            return

def last_mod_timestamp(name):
    data = emperor_stats()
    for vassal in sorted(data['vassals'], key=lambda x: x['id']):
        if name == vassal['id'].split('.')[0]:
            return vassal['last_mod']
    return 0

def vassal_accepting(name):
    data = emperor_stats()
    for vassal in sorted(data['vassals'], key=lambda x: x['id']):
        if name == vassal['id'].split('.')[0]:
            if vassal['accepting'] == 1:
                return True
            else:
                return False
    return False

def is_subscribed_to_fastrouter(name):
    data = fastrouter_stats()
    for subscription in data['subscriptions']:
        for node in subscription['nodes']:
            if node['name'].split('/')[-1].split('.')[0] == name and node['death_mark'] == 0:
                return True
    return False

def reload_vassals(ini_files):
    """
    reload all the corresponding vassals in parallel
    """
    vassal_last_mod_timestamp = {}
    vassal_stopped = {}
    start_timestamp = time.time()
    names = []
    if isinstance(ini_files, basestring):
        ini_files = [ini_files]
    for ini_file in ini_files:
        name = ini_file.split('/')[-1].split('.')[0]
        names.append(name)
        vassal_last_mod_timestamp[name] = last_mod_timestamp(name)
        vassal_stopped[name] = False
        #print_vassal_info(name)
        # trigger the reload
        subprocess.call(['touch', '-h', ini_file])
        #print_vassal_info(name)
    while names:
        for name_index, name in enumerate(names):
            if not vassal_stopped[name] and last_mod_timestamp(name) != vassal_last_mod_timestamp[name]:
                vassal_stopped[name] = True
            if vassal_stopped[name] and vassal_accepting(name) and is_subscribed_to_fastrouter(name):
                #print_vassal_info(name)
                del names[name_index]
                if not args.quiet:
                    #print_vassal_info(name)
                    print('%s: reloaded' % name)
                break
            if time.time() - start_timestamp >= args.timeout:
                del names[name_index]
                if not args.quiet:
                    #print_emperor_stats(name)
                    #print_fastrouter_stats(name)
                    print('%s: timeout reached' % name)
                break
        time.sleep(args.check_interval)

ini_files = sorted([os.path.join(args.emperor_path, f) for f in os.listdir(args.emperor_path) if f.endswith(args.vassal_config_file_suffix)])

num_vassals = len(ini_files)
if num_vassals > (args.minimum_active_vassals + 1):
    parallel_reload = ini_files[: num_vassals - args.minimum_active_vassals]
    serial_reload = ini_files[- args.minimum_active_vassals :]
else:
    parallel_reload = []
    serial_reload = ini_files

if parallel_reload:
    reload_vassals(parallel_reload)
for ini_file in serial_reload:
    reload_vassals(ini_file)

