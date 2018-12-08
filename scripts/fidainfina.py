# Fix dates in filename
from __future__ import print_function

from os import listdir, rename
from os.path import isfile, join
import os
import sys

if sys.version_info > (2, 7):
    def unicode(s, _):
        return s

if os.name == 'nt':
    import win32api, win32con
    
pivot_year = 1969
century = int(str(pivot_year)[:2]) * 100


def file_is_hidden(p):
    if os.name== 'nt':
        attribute = win32api.GetFileAttributes(p)
        return attribute & (win32con.FILE_ATTRIBUTE_HIDDEN | win32con.FILE_ATTRIBUTE_SYSTEM)
    else:
        return p.startswith('.') #linux-osx


def year_2to4_digit(year):
    return century + year if century + year > pivot_year else (century + 100) + year


def fix_dates_in_folder(mypath):
    for f in listdir(mypath):
        y, m, d = 0, 13, 32
        file_path = join(mypath, f)
        try:
            f = unicode(f, 'utf-8')
            if isfile(file_path):
                for l in [8, 6]:
                    if f[:l].isnumeric():
                        y, m, d = map(int, (f[:l-4], f[l-4:l-2], f[l-2:l]))
                        break
                if y < 100:
                    y = year_2to4_digit(y)
                if y and m < 13 and d < 32:
                    newfilename = "%04d-%02d-%02d" % (y, m, d) + f[l:].lstrip()
                    print(newfilename)
                    rename(file_path, join(mypath, newfilename))
        except UnicodeDecodeError:
            pass


if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1]:
            fix_dates_in_folder(sys.argv[1])