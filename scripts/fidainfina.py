#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Fix dates in filename, enforces ISO 8601 at folders given in arguments
from __future__ import print_function

import sys
from os import listdir, rename
from os.path import isfile, join, splitext
import os
import stat
import re
from datetime import datetime
import itertools


if sys.version_info > (2, 7):
    def unicode(s, _):
        return s

pivot_year = 1969
century = int(str(pivot_year)[:2]) * 100


def file_is_hidden(filepath):
    return bool(os.stat(filepath).st_file_attributes & stat.FILE_ATTRIBUTE_HIDDEN)


def year_2to4_digit(year):
    return century + year if century + year > pivot_year else (century + 100) + year


def get_numbers(str):
    """Returns numeric charachters  in string"""
    num = ''
    cnt = 0
    for char in str:
        if char.isnumeric():
            num += char
            cnt += 1
    return num


def fix_dates_in_folder(mypath):
    for f in listdir(mypath):
        y, m, d = 0, 13, 32
        file_path = join(mypath, f)
        if isfile(file_path) and not file_is_hidden(file_path):
            try:
                f = unicode(f, 'utf-8')

                if not re.match(r'^\d{4}-\d{2}-\d{2}', f):
                    mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime = os.stat(file_path)
                    atime = datetime.utcfromtimestamp(atime)
                    mtime = datetime.utcfromtimestamp(mtime)
                    ctime = datetime.utcfromtimestamp(ctime)
                    diff_last = 0x10000000000
                    remfilename = ''
                    result = 0
                    fname_old, _ = splitext(f)
                    for str in re.split(r'[ _]', fname_old):  # substrings
                        str_digits = ''.join(c for c in str if c.isnumeric())

                        if len(str_digits) == 6:
                            pair1 = str_digits[0:2]
                            pair2 = str_digits[2:4]
                            pair3 = str_digits[4:6]
                        elif len(str_digits) == 8:
                            pair1 = str_digits[0:4]
                            pair2 = str_digits[4:6]
                            pair3 = str_digits[6:8]
                        if len(str_digits) in [6, 8]:
                            format = "%y.%m.%d" if len(str_digits) == 6 else "%Y.%m.%d"
                            choices = (pair1, pair2, pair3)
                            for choice in itertools.permutations(choices):
                                y, m, d = map(int, choice)
                                if y and m < 13 and d < 32:
                                    choice = '.'.join(choice)
                                    guess = datetime.strptime(choice, format)
                                    for filetime in [atime, mtime, ctime]:
                                        diff = abs((guess - filetime).total_seconds())
                                        if diff < diff_last:
                                            diff_last = diff
                                            result = guess
                                            f_time = filetime
                                            remfilename = str

                    if result and remfilename:
                        newfilename = f.replace(remfilename, '')
                        fname, f_ext = splitext(newfilename)
                        fname = fname.rstrip()
                        for strip in ['_']:
                            fname = fname.rstrip(strip).lstrip(strip)
                        newfilename = result.strftime('%Y-%m-%d') + '_' + fname + f_ext
                        print(f.ljust(60), remfilename.ljust(15), f_time, diff_last // 84600, newfilename)
                        rename(file_path, join(mypath, newfilename))
            except UnicodeDecodeError:
                pass


if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1]:
            fix_dates_in_folder(sys.argv[1])