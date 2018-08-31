#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
import platform, struct, socket, threading, re, requests, json, sys
import netifaces as ni
from subprocess import Popen, PIPE
from os.path import isfile
if sys.version_info < (3, 0):
    import thread as _thread
else:
    import _thread

PATADR = '((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)'
PATMAC = '([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})'
if platform.system() == 'Linux':
    from netifaces import AF_INET, AF_INET6, AF_LINK, AF_PACKET, AF_BRIDGE
    PINGARG = '-c'
    ARPARG = '-n'
else:
    PINGARG = '-n'
    ARPARG = '-a'
PATARP = '(' + PATADR + ')\s+(' + PATMAC + ')\s+(\w+)'  # May need different for linux...

def netmask_to_cidr(netmask):  # code to convert netmask ip to cidr number
    '''
    :param netmask: netmask ip addr (eg: 255.255.255.0)
    :return: equivalent cidr number to given netmask ip (eg: 24)
    '''
    return sum([bin(int(x)).count('1') for x in netmask.split('.')])

def cidr_to_range(ip, cidr):
    cidr = int(cidr)
    host_bits = 32 - cidr
    i = struct.unpack('>I', socket.inet_aton(ip))[0]  # note the endianness
    start = (i >> host_bits) << host_bits  # clear the host bits
    end = start | ((1 << host_bits) - 1)
    return start, end

def ping(host):
    toping = Popen(['ping', PINGARG, '3', host], stdout = PIPE)
    output = toping.communicate()[0]
    return bool(toping.returncode == 0)

def TCP_connect(ip, port, delay, output):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.settimeout(delay)
    try:
        sock.connect((ip, port))
        # host = socket.gethostbyaddr(ip)
        if ip not in output:
            output[ip] = []
        if port not in output[ip]:
            output[ip].append(port)
    except:
        pass

OUIS = {}
if isfile('oui.json'):
    with open('oui.json', 'r') as fp:
        OUIS = json.load(fp)
else:
    URL_oui = 'http://standards-oui.ieee.org/oui.txt'
    print('Fetching oui')
    r = requests.get(URL_oui)
    for line in r.iter_lines():
        if b'(hex)' in line:
            if sys.version_info < (3, 0):
                line = str(line)
            else:
                line = str(line, 'utf-8')
            key, val = list(map(str.strip, line.split('(hex)')))
            OUIS[key] = val
    with open('oui.json', 'w') as fp:
        json.dump(OUIS, fp)


ports = [21, 22, 23, 5554, 5555]
delay = 0.5
threads = []  # To run TCP_connect concurrently
output = {}  # For printing purposes

for iface in ni.interfaces():
    for k,v in ni.ifaddresses(iface).items():
        if k is 2:
            for item in v:
                if all(c in item for c in ('addr', 'netmask')) and item['addr'] != '127.0.0.1':
                    addr, netmask, _ = item.values()
                    cidr = netmask_to_cidr(netmask)
                    start, end = cidr_to_range(addr, cidr)
                    for i in range(start, end):
                        ip = socket.inet_ntoa(struct.pack('>I', i))
                        for port in ports:
                            t = threading.Thread(target=TCP_connect, args=(ip, port, delay, output))
                            threads.append(t)
                            thasstarted = False
                            while not thasstarted:
                                try:
                                    t.start()
                                    thasstarted = True
                                except _thread.error:
                                    pass
                                    # print(threading.active_count(), thasstarted)

# arp list
p = Popen(['arp', ARPARG], stdout=PIPE, stderr=PIPE)
out, err = p.communicate()
txt = str(out) if sys.version_info < (3, 0) else str(out, encoding='ascii')

MACS = {}
for i in re.findall(PATARP, txt):
    MACS[i[0]] = i[4]

# Locking the script until all threads complete
print('Waiting for threads...')
for t in threads:
    t.join()

for k, v in output.items():
    if v:
        mac = MACS[k] if k in MACS else ''
        oui = mac[:8].upper()
        prod = OUIS[oui] if oui in OUIS else ''
        print(k.ljust(15), mac, v, prod)



