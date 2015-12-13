#!/usr/bin/env python3

import fileinput

"""Prints (short hash, file size) pairs in a datafile generated with the
file_counts.py script."""

for line in fileinput.input():
    hsh, count, size = line.strip().split("  ")
    sh = int(hsh, 16) >> (160 - 13)
    print("%i|%s" % (sh, size))
