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
import collections
import operator
import random
import recordclass
import sys
import timer
import utils

DESCRIPTION = """A simulator for the deduplication protocol."""

# A single file in the simulation
File = recordclass.recordclass("File",
                               "hash checks_available copies threshold")


@utils.timeit
def simulate(args):
    if args.rlc <= 0 and args.rlu <= 0:
        raise Exception("--pake-runs or --check-limit must be positive")

    elif args.rlc <= 0:
        args.rlc = 100 - args.rlu
        print("Implicitly setting RLc = %i" % args.rlc, file=sys.stderr)

    elif args.rlu <= 0:
        args.rlu = 100 - args.rlc
        print("Implicitly setting RLu = %i" % args.rlu, file=sys.stderr)

    # A dict of bucket_id -> [File, File, ..., File] for each bucket
    buckets = collections.defaultdict(list)

    # The number of bytes saved to the storage
    data_in_storage = 0

    # The number of bytes uploaded through the protocol before deduplication
    data_uploaded = 0

    tmr = timer.Timer()
    for (i, (upload, size)) in enumerate(utils.read_upload_stream()):
        data_uploaded += 1 if args.percentage_with_counts else size

        if (i + 1) % utils.REPORT_FREQUENCY == 0:
            percentage = 1 - data_in_storage / data_uploaded
            print("%s uploads, percentage %.4f, time %s, %s" % (
                utils.num_fmt(i),
                percentage,
                tmr.elapsed_str,
                utils.get_mem_info()
            ), file=sys.stderr)

            tmr.reset()

        # Get the short hash.
        short_hash = upload >> (args.hashlen - args.shlen)

        if args.with_sizes:
            bucket_id = short_hash | size << args.shlen
        else:
            bucket_id = short_hash

        # The list of the files in the bucket in the order of their popularity
        files = buckets[bucket_id]

        # If the upload was deduplicated.
        file_deduplicated = False
        match_found = False
        match_index = 0

        # The number of files considered for deduplication
        files_considered = 0

        for i, fl in enumerate(files):
            if fl.checks_available < 1:
                # This file no longer has checkers. Skip it.
                # TODO: Check if these could be removed from the array or is
                # removal too expensive
                continue

            files_considered += 1

            # If this is the uploaded file but has already been
            # deduplicated as a different file, the second match is just
            # ignored
            if fl.hash == upload and not file_deduplicated and not match_found:
                match_found = True
                match_index = i

                # Check if the threshold has already been met and deduplicate
                # if it has
                if args.deduplicate_below_threshold or fl.copies >= fl.threshold:
                    # Deduplication \o/
                    file_deduplicated = True

                    # This "uploader" will perform RL_c checks for this file.
                    fl.checks_available += args.rlc

                # The popularity of this file went up by 1
                fl.copies += 1

            # A check was performed against this file.
            fl.checks_available -= 1

            if files_considered == args.rlu:
                # The uploader rate limit has been reached.
                break

        if not file_deduplicated:
            # The upload could not be deduplicated.
            data_in_storage += 1 if args.percentage_with_counts else size

            # Add the file to the list of files in this bucket.
            files.append(File(
                hash=upload,
                checks_available=args.rlc,
                copies=1,
                threshold=random.randint(2, args.max_threshold)
            ))

        # The matching file had its popularity increase. Make the list
        # sorted again by shifting the item left until the list is ordered.
        while match_found and match_index > 0 and \
                files[match_index - 1].copies < files[match_index].copies:

            files[match_index - 1], files[match_index] = \
                files[match_index], files[match_index - 1]

            match_index -= 1

        if not args.only_final:
            # Print the number to files to the output file
            print("%i,%i" % (data_in_storage, data_uploaded))

    dedup_percentage = 1 - data_in_storage / data_uploaded

    # Print the results if asked to. If this was false, the progress has been
    # printed as files were being uploaded.
    if args.only_final:
        print("%s,%s,%s,%s" % (
            args.rlc,
            args.rlu,
            args.max_threshold,
            dedup_percentage)
        )

    print("+++ Done. stored=%s, uploaded=%s, dedup_percentage=%f" % (
        utils.sizeof_fmt(data_in_storage), utils.sizeof_fmt(data_uploaded),
        dedup_percentage), file=sys.stderr)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument("--short-hash-length",
                        dest="shlen", action="store", default=13, type=int,
                        help="The length of short hash in bits.")
    parser.add_argument("--pake-runs",
                        dest="rlu", action="store", default=30, type=int,
                        help="The number of files that are considered when " +
                             "uploading a new file (RL_u).")
    parser.add_argument("--hash-length",
                        dest="hashlen", action="store", default=160, type=int,
                        help="The length of the dataset hashes in bits.")
    parser.add_argument("--check-limit",
                        dest="rlc", action="store", default=70, type=int,
                        help="The number of times an uploader can perform a " +
                             "check for a file (RL_c).")
    parser.add_argument("--max-threshold",
                        action="store", default=20, type=int,
                        help="The maximum value for the random threshold")
    parser.add_argument("--with-sizes", action="store_true",
                        help="Use size information of the files in the " +
                        "protocol.")
    parser.add_argument("--percentage-with-counts", action="store_true",
                        help="If specified, the deduplication percentage is " +
                        "calculated based on file counts instead of their " +
                        "sizes.")
    parser.add_argument("--deduplicate-below-threshold", action="store_true",
                        help="If specified, deduplication occurs even if the " +
                        "number of copies is below the threshold")
    parser.add_argument("--only-final", action="store_true",
                        help="Only print final results from the simulation. " +
                        "The format of that line is: " +
                        "<RLc>,<RLu>,<max_threshold>,<dedup_percentage>")
    simulate(parser.parse_args())
