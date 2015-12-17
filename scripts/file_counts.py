#!/usr/bin/env python
#
# Copyright 2015 Secure Systems Group, Aalto University https://se-sy.org/.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import hashlib
import os
import os.path
import stat
import sys

"""
A script for counting file popularity information in given directory.

Usage:
    ./file_counts.py DIRECTORY

The popularity data will be written to stdout. Each line contains information
about a single file in the following format:
    <SHA-1 HASH> <COUNT> <SIZE>

Here:
* SHA-1 HASH = the hash of the file contents
* COUNT = the number of copies this file had in the given directory
* SIZE = the size of the file in bytes

"""

data = {}

if len(sys.argv) < 2:
    print "Usage: %s directory" % sys.argv[0]
    sys.exit(1)

directory = sys.argv[1]

if not os.path.isdir(directory):
    print "%s is not a directory." % directory
    sys.exit(1)


def fhash(f):
    hasher = hashlib.sha1()
    try:
        with open(f, "rb") as fd:
            for chunk in iter(lambda: fd.read(2048), ''):
                hasher.update(chunk)
    except IOError:
        return None

    return hasher.hexdigest()

for root, dirs, files in os.walk(directory):
    if root.startswith("/proc") or root.startswith("/sys"):
        continue

    if root.startswith("/dev"):
        continue

    for f in files:
        path = os.path.join(root, f)
        try:
            st = os.stat(path)
        except OSError:
            continue
        if not stat.S_ISREG(st.st_mode):
            continue

        sha1 = fhash(path)
        if sha1 is None:
            continue

        size = st.st_size
        identifier = "%s|%i" % (sha1, size)

        if identifier in data:
            data[identifier] += 1
        else:
            data[identifier] = 1

for identifier, count in data.iteritems():
    sha1, size = identifier.split("|")
    print "%s  %s  %s" % (sha1, count, size)
