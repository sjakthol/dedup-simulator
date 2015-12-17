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

import fileinput

"""Prints short hashes of files in a datafile generated with the file_counts.py
script."""

for line in fileinput.input():
    hsh, count, size = line.strip().split("  ")
    sh = int(hsh, 16) >> (160 - 13)
    print(sh)
