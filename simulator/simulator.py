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
import sys
import timer
import utils

DESCRIPTION = """A simulator for the deduplication protocol."""


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

    # A dict of short_hash -> [{ file, checks_available, copies }] for at most
    # RLu most common files for the short hash.
    # * file = hash of the file
    # * checks_available = number of checks the uploaders can make
    # * copies = the popularity of the file
    sh_most_common_files = {}

    # A dict of short_hash -> collections.deque([f1, f2, f3, ...]) for files
    # that have been uploaded but not deduplicated. If one of the most_common
    # files runs out of checkers one of these files will be selected to replace
    # that one.
    sh_uncommon_files = {}

    data_in_storage = 0
    data_uploaded = 0

    tmr = timer.Timer()
    for (i, (upload, size)) in enumerate(utils.read_upload_stream()):
        data_uploaded += size

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

        # Check if this is the first time a file with this short has is
        # uploaded.
        if bucket_id not in sh_most_common_files:
            # Create the most common list for this short hash and size
            sh_most_common_files[bucket_id] = []

            # Create the uncommon file list for this short hash
            sh_uncommon_files[bucket_id] = collections.deque()

        # The list of RLu most common files.
        most_common = sh_most_common_files[bucket_id]

        # If the upload was deduplicated.
        file_deduplicated = False
        needs_most_common_sort = False

        for data in most_common:
            # If this is the uploaded file but has already been
            # deduplicated as a different file, the second match is just
            # ignored
            if data["file"] == upload and not file_deduplicated:
                if data["threshold"] < data["copies"]:
                    # This was a match but the threshold has not been met. The
                    # uploader receives a random key and uploads a new file to
                    # the server. However, since we know that the file about to
                    # be uploaded is a copy of this file, we increase the count
                    # for that file
                    data["copies"] += 1
                else:
                    # Deduplication \o/
                    file_deduplicated = True

                    # This "uploader" will perform RL_c checks for this file.
                    data["checks_available"] += args.rlc

                    # The popularity of this file went up by 1
                    data["copies"] += 1

                    needs_most_common_sort = True

            # A check was performed against this file.
            data["checks_available"] -= 1

            #assert data["checks_available"] >= 0
            #assert data["copies"] >= 1

        if not file_deduplicated:
            # The upload could not be deduplicated.
            data_in_storage += size

            # Add the file to the end of the list of uncommon files
            sh_uncommon_files[bucket_id].append(upload)

        # Remove files that have no more checkers available
        new_most_common = filter(operator.itemgetter("checks_available"),
                                 most_common)

        if needs_most_common_sort:
            # Sort the most common files by popularity. Since all new files
            # that might be added to the list have only one copy this can be
            # done here, before those are appended to the list.
            new_most_common = sorted(new_most_common,
                                     key=operator.itemgetter("copies"),
                                     reverse=True)
        else:
            new_most_common = list(new_most_common)

        # Check if some files ran out of checkers and add new ones.
        new_files_needed = args.rlu - len(new_most_common)
        if new_files_needed > 0:
            # The list of most common files is not full.
            uncommon_files = sh_uncommon_files[bucket_id]

            # Add new files to the list until either a) there's enough
            # files or b) there's no more uncommon files to add
            while new_files_needed > 0 and uncommon_files:
                new_file = uncommon_files.popleft()

                # Add the file to the list of most common files. Since this
                # file was not deduplicated earlier the server only knows a
                # single user who has uploaded this file. Thus it has one
                # copy and checks of that user available.
                new_most_common.append({
                    "file": new_file,
                    "checks_available": args.rlc,
                    "copies": 1,
                    "threshold": random.randint(2, args.max_threshold)})

                new_files_needed -= 1

        assert len(new_most_common) <= args.rlu

        # Update the most_common mapping
        sh_most_common_files[bucket_id] = new_most_common

        # Print the number to files to the output file
        print("%i,%i" % (data_in_storage, data_uploaded))

    dedup_percentage = 1 - data_in_storage / data_uploaded
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
    simulate(parser.parse_args())
