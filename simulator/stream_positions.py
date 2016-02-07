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

"""
A script that prints the positions of the uploads in the stream.

Usage:
  ./stream_positions.py <hash>

Output:
   Integer indexes separated with newlines.
"""

import sys
import utils


def main():
    hsh = int(sys.argv[-1], 16)

    for (i, (upload, size)) in enumerate(utils.read_upload_stream()):
        if upload == hsh:
            print(i)

if __name__ == "__main__":
    main()
