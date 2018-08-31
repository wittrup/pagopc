#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Will download all config from /Hard%20Disk/LogFiles/Common/ or /DiskOnChip/LogFiles/Common/"""


from ftplib import FTP
from os import getcwd, mkdir
from os.path import join as pathjoin, exists, isabs as pathisabs, dirname, abspath, split as pathsplit
import argparse


# TODO:
# - argsparser for overwriting username & password?
# - only store with new timestamp if changes
# - add exception handler output to try clause


def ftpcopy(filename, local_filename):
    file = open(local_filename, 'wb')
    ftp.retrbinary('RETR ' + filename, file.write)
    file.close()

def splitall(path):
    allparts = []
    while 1:
        parts = pathsplit(path)
        if parts[0] == path:  # sentinel for absolute paths
            allparts.insert(0, parts[0])
            break
        elif parts[1] == path: # sentinel for relative paths
            allparts.insert(0, parts[1])
            break
        else:
            path = parts[0]
            allparts.insert(0, parts[1])
    return allparts


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Will download all config from /Hard%20Disk/LogFiles/Common/ or /DiskOnChip/LogFiles/Common/')
    parser.add_argument(dest='host', type=str, help="hostname for device")
    parser.add_argument(dest='dest', type=str, help="destination folder")
    args = parser.parse_args()

    credentialspath = pathjoin(dirname(abspath(__file__)) ,r'../ignore/credentials.txt')
    assert exists(credentialspath), "credentials file not found " + credentialspath + " - optionals method not implemented"
    username, password = [line.rstrip() for line in open(credentialspath).readlines()]

    ftp = FTP(args.host)
    ftp.login(username, password)

    for subfolder in ["DiskOnChip", "Hard Disk", "LogFiles", "Common"]:
        if subfolder.lower() in list(map(str.lower, ftp.nlst())):
            ftp.cwd(subfolder)

    path = args.dest
    if not pathisabs(path):
        path = abspath(pathjoin(getcwd(), path))
    for item in [ftp.host] + list(splitall(ftp.pwd())):
        item = item.replace('/', '').replace(r'\\', '')
        if item not in path:
            path = pathjoin(path, item)
    if not exists(path):
        mkdir(path)

    print('Copying from', ftp.pwd())
    i = 0
    for filename in ftp.nlst(): # get filenames within the directory
        try:
            local_filename = pathjoin(path, filename)
            file = open(local_filename, 'wb')
            ftp.retrbinary('RETR ' + filename, file.write)
            file.close()
        except:
            print('FAILED', filename)
        finally:
            i += 1
            print(filename)
    print("        %i file(s) copied." % i)
    ftp.quit() # This is the “polite” way to close a connection
