#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Will download all config from /Hard%20Disk/LogFiles/Common/ or /DiskOnChip/LogFiles/Common/"""


from ftplib import FTP
from os import getcwd, makedirs, remove as delfile
from os.path import join as pathjoin, exists, isabs as pathisabs, dirname, abspath, split as pathsplit, getsize
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
        makedirs(path)

    print('Copying from ' + ftp.pwd())
    i = 0
    fails = []
    files = sorted(ftp.nlst())
    last = len(files) - 2  # to copy last file
    for n, filename in enumerate(files):  # get filenames within the directory
        local_filename = pathjoin(path, filename)
        if n > last or (not exists(local_filename)) or (exists(local_filename) and not getsize(local_filename)):
            try:
                file = open(local_filename, 'wb')
                ftp.retrbinary('RETR ' + filename, file.write)
                i += 1
                print(filename)
            except Exception as e:
                file.close()
                if exists(local_filename):
                    delfile(local_filename)
                fails.append(('FAILED', filename, str(e)))
            finally:
                file.close()
    print("        %i file(s) copied." % i)
    ftp.quit()  # This is the “polite” way to close a connection
    for fail in fails:
        print(fail)
