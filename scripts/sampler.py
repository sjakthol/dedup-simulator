#!/usr/bin/env python3
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

import argparse
import fileinput
import sys

"""
Reads lines from stdin and takes a constant number of samples from it. The
samples are written to stdout with following format:

  <LINE NUMBER>,<SAMPLE>

Since the number of samples is constant, you need to provide the total number
of lines in the output to this script.
"""

parser = argparse.ArgumentParser(description="Sampler")
parser.add_argument("--samples",
                    dest="samples",
                    action="store",
                    default=10000,
                    type=int,
                    help="The number of samples to take.")

parser.add_argument("--total-lines",
                    dest="lines",
                    action="store",
                    type=int,
                    help="The number of entries in the data.")

args = parser.parse_args()
nth = int(args.lines / args.samples)

print("Taking %i samples from %i entries (every %ith)" % (
      args.samples, args.lines, nth), file=sys.stderr)
i = 1
last = None
for line in fileinput.input("-"):
    if i % nth == 0 or i == 1:
        print("%i,%s" % (i, line.strip()))

    last = line.strip()

    i += 1

if last and (i - 1) % nth != 0:
    print("%i,%s" % (i-1, line))

if i - 1 != args.lines:
    print("WARNING: The total number of lines was wrong.", file=sys.stderr)
