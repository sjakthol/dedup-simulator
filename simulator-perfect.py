#!/usr/bin/env python3
import timer
import sys
import utils


def simulate():
    # A set of files already in the storage
    seen = set()

    # The size of the all uploads combined (deduplicated or not)
    total_in = 0

    # The size of the data sent to the service
    data_in = 0

    tmr = timer.Timer()
    for (i, (hsh, size)) in enumerate(utils.read_upload_stream()):
        total_in += size
        if hsh not in seen:
            data_in += size
            seen.add(hsh)

        if (i + 1) % utils.REPORT_FREQUENCY == 0:
            print("%s uploads, percentage %.4f, time %s, mem[%s]" % (
                utils.num_fmt(i),
                1 - data_in / total_in,
                tmr.elapsed_str,
                utils.get_mem_info()
            ), file=sys.stderr)

        print("%i,%i" % (data_in, total_in))

    dedup_percentage = 1 - data_in / total_in
    print("Simulation complete. stored=%s, uploaded=%s, dedup_percentage=%f" % (
        utils.sizeof_fmt(data_in), utils.sizeof_fmt(total_in), dedup_percentage),
        file=sys.stderr)

if __name__ == "__main__":
    simulate()
