#!/usr/bin/env python3
import gzip
import itertools
import timer
import sys
import utils


# A set of files already in the storage
seen = set()

# The total number of uploads
total_uploads = 0

# The number of files in the storage
files_in = 0

tmr = timer.Timer()
for (hsh, _) in utils.read_upload_stream():
    if hsh not in seen:
        files_in += 1
        seen.add(hsh)
    total_uploads += 1

    if total_uploads % utils.REPORT_FREQUENCY == 0:
        print("%s uploads, percentage %.4f, time %s, %s" % (
            utils.num_fmt(total_uploads),
            1 - files_in / total_uploads,
            tmr.elapsed_str,
            utils.get_mem_info()
        ), file=sys.stderr)

dedup_percentage = 1 - files_in / total_uploads
print("+++ Simulation complete. dedup_percentage=%f" % dedup_percentage, file=sys.stderr)
