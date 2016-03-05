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

import timer
import sys
import utils


def simulate():
    # A set of files already in the storage
    seen = set()

    files_uploaded = 0
    data_uploaded = 0
    files_in_storage = 0
    data_in_storage = 0

    tmr = timer.Timer()

    def print_stats():
        data = (
            utils.num_fmt(files_in_storage),
            utils.num_fmt(files_uploaded),
            1 - files_in_storage / files_uploaded,
            utils.sizeof_fmt(data_in_storage),
            utils.sizeof_fmt(data_uploaded),
            1 - data_in_storage / data_uploaded,
            utils.get_mem_info(),
            tmr.elapsed_str
        )

        tmpl = (
            "Statistics: \n"
            "  Files: files_in_storage=%s, files_uploaded=%s, DDP=%s\n"
            "  Data: data_in_storage=%s, data_uploaded=%s, DDP=%s\n"
            "  Execution: memory[%s], chunk_time=%s"
        )

        tmr.reset()

        print(tmpl % data, file=sys.stderr)

    for (i, (hsh, size)) in enumerate(utils.read_upload_stream()):
        files_uploaded += 1
        data_uploaded += size
        if hsh not in seen:
            files_in_storage += 1
            data_in_storage += size
            seen.add(hsh)

        if (i + 1) % utils.REPORT_FREQUENCY == 0:
            print_stats()

        print("%i,%i,%i,%i" % (
            files_in_storage,
            files_uploaded,
            data_in_storage,
            data_uploaded,
        ))

    print("+++ Done; ", end="", file=sys.stderr)
    print_stats()

if __name__ == "__main__":
    simulate()
