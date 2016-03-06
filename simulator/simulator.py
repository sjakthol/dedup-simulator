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
import math
import operator
import random
import recordclass
import sys
import timer
import utils

DESCRIPTION = """A simulator for the deduplication protocol. The following
statline is printed to the standard output after each upload:
    <files_in_storage>,<files_uploaded>,<data_in_storage>,<data_uploaded>

Redirecting the stdout to a file will produce a valid CSV file with the raw
simulation resuts.

If the flag --only-final is used, no results are printed during simulations but
the final deduplication percentage is outputted with the simulation parameters
after all files have been uploaded. That line has following format (no newline
in the actual output):
    <RLc>,<RLu>,<max_threshold>,<offline_rate>
    <dedup_percentage_based_on_file_counts>,<dedup_percentage_based_on_bytes>

"""

# A single file in the simulation
File = recordclass.recordclass("File",
                               "hash checkers copies threshold")


@utils.timeit
#@profile
def simulate(args):
    # A dict of bucket_id -> [File, File, ..., File] for each bucket
    buckets = collections.defaultdict(list)

    # The number of bytes saved to the storage
    data_in_storage = 0
    files_in_storage = 0

    # The number of bytes uploaded through the protocol before deduplication
    data_uploaded = 0
    files_uploaded = 0

    tmr = timer.Timer()
    tmr_start = timer.Timer()

    def print_stats():
        """A helper for printing statistics about the simulation"""
        data = (
            args.rlc,
            args.rlu,
            args.max_threshold,
            args.offline_rate,
            utils.num_fmt(files_in_storage),
            utils.num_fmt(files_uploaded),
            1 - files_in_storage / files_uploaded,
            utils.sizeof_fmt(data_in_storage),
            utils.sizeof_fmt(data_uploaded),
            1 - data_in_storage / data_uploaded,
            utils.get_mem_info(),
            tmr.elapsed_str,
            tmr_start.elapsed_str,
        )

        tmpl = (
            "Statistics: \n"
            "  Params: RLc=%s, RLu=%s, max_threshold=%s, offline_rate=%s\n"
            "  Files: files_in_storage=%s, files_uploaded=%s, DDP=%s\n"
            "  Data: data_in_storage=%s, data_uploaded=%s, DDP=%s\n"
            "  Execution: memory[%s], chunk_time=%s, total_time=%s"
        )

        tmr.reset()

        print(tmpl % data, file=sys.stderr)

    llen = len
    for (i, (upload, size)) in enumerate(utils.read_upload_stream()):
        data_uploaded += size
        files_uploaded += 1

        if (i + 1) % utils.REPORT_FREQUENCY == 0:
            print_stats()

        # Get the short hash.
        short_hash = upload >> (args.hashlen - args.shlen)

        bucket_id = short_hash
        if args.with_sizes:
            bucket_id |= size << args.shlen

        # The list of the files in the bucket in the order of their popularity
        files = buckets[bucket_id]

        # If the upload was deduplicated.
        file_deduplicated = False
        match_found = False
        match_index = 0

        # The number of files considered for deduplication
        files_considered = 0

        for i, fl in enumerate(files):
            if not fl.checkers:
                # This file no longer has checkers. Skip it.
                # TODO: Check if these could be removed from the array or is
                # removal too expensive
                continue

            # The checkers for this file
            checkers = fl.checkers

            # Calculate how many checkers there are available
            num_checkers = llen(checkers)

            # Calculate the propability of all available checkers being online.
            # Since P(checker offline) = args.offline_rate / 100,
            # P(all checkers offline)
            #   = P(c1 offline) AND P(c2 offline) ... P(cn offline)
            #   = P(c1 offline) * P(c2 offline)* ... * P(cn offline)
            #   = P(checker offline) ^ n
            if args.offline_rate and \
                    random.random() < math.pow(args.offline_rate, num_checkers):
                # All checkers were offline, try the next one
                continue

            files_considered += 1

            # The last checker in the list has performed the least number of
            # checks
            checker_index = num_checkers - 1

            # Decrease the check count for the checker.
            checkers[checker_index] -= 1

            # If this is the uploaded file but has already been
            # deduplicated as a different file, the second match is just
            # ignored
            if fl.hash == upload and not match_found:
                match_found = True
                match_index = i

                # Deduplication occurs if
                # (1) we deduplicate even below threshold or
                # (2) we are above the threshold
                if args.deduplicate_below_threshold or fl.copies >= fl.threshold:
                    # Deduplication \o/
                    file_deduplicated = True

                # The popularity of this file went up by 1
                fl.copies += 1

                if args.one_successful_check and file_deduplicated:
                    # A successful check; this checker replaces the client who
                    # performed the check for this upload.
                    checkers[checker_index] = args.rlc
                else:
                    # This "uploader" will perform RLc checks for this file.
                    # This also happens if the threshold has not yet been met.
                    # In that case the uploader just uses a different key when
                    # deduplicating this file
                    checkers += [args.rlc]

            if checkers[checker_index] == 0:
                # The checker has hit the limit;
                checkers.pop(checker_index)

            elif num_checkers > 1 and checkers[checker_index] != args.rlc:
                # The uploader did not replace the checker. Sort the list.
                checkers.sort()

            # assert all(checkers[i] <= checkers[i+1] for i in range(len(checkers)-1))

            if files_considered == args.rlu:
                # The uploader rate limit has been reached.
                break

        if not file_deduplicated:
            # The upload could not be deduplicated.
            data_in_storage += size
            files_in_storage += 1

        # There was no match for this file. Add a new file to the bucket.
        if not match_found:
            # Add the file to the list of files in this bucket.
            files.append(File(
                hash=upload,
                # The list of checkers for this file; each entry is the number
                # of checks that checker has available
                checkers=[args.rlc],
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

        # assert all(files[i].copies >= files[i+1].copies for i in range(len(files)-1))

        if not args.only_final:
            # Print the number to files to the output file
            print("%i,%i,%i,%i" % (
                files_in_storage,
                files_uploaded,
                data_in_storage,
                data_uploaded,
            ))

    # Print the results if asked to. If this was false, the progress has been
    # printed as files were being uploaded.
    if args.only_final:
        print("%s,%s,%s,%s,%s,%s" % (
            args.rlc,
            args.rlu,
            args.max_threshold,
            args.offline_rate,
            1 - files_in_storage / files_uploaded,
            1 - data_in_storage / data_uploaded,
        ))

    print("+++ Done - ", file=sys.stderr, end="")
    print_stats()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    params = parser.add_argument_group("Protocol Parameters")
    params.add_argument("--short-hash-length",
                        dest="shlen", action="store", default=13, type=int,
                        help="The length of short hash in bits.")
    params.add_argument("--hash-length",
                        dest="hashlen", action="store", default=160, type=int,
                        help="The length of the dataset hashes in bits.")

    params.add_argument("--check-limit",
                        dest="rlc", action="store", default=70, type=int,
                        help="The number of times an uploader can perform a " +
                             "check for a file (RL_c).")
    params.add_argument("--pake-runs",
                        dest="rlu", action="store", default=30, type=int,
                        help="The number of files that are considered when " +
                             "uploading a new file (RL_u).")
    params.add_argument("--max-threshold",
                        action="store", default=20, type=int,
                        help="The maximum value for the random threshold")
    params.add_argument("--offline-rate", action="store", default=0, type=float,
                        help="The probability that a client is offline " +
                        "during an upload.")

    protof = parser.add_argument_group(
        "Protocol Version",
        "These arguments change the protocol to be used for this simulation.")
    protof.add_argument("--one-successful-check", action="store_true",
                        help="Checkers stop performing checks after they " +
                        "have performed one successful check")
    protof.add_argument("--with-sizes", action="store_true",
                        help="Use size information of the files in the " +
                        "protocol.")
    protof.add_argument("--deduplicate-below-threshold", action="store_true",
                        help="If specified, deduplication occurs even if the " +
                        "number of copies is below the threshold")

    parser.add_argument(
        "--only-final", action="store_true",
        help=("Only print final results from the simulation. The format of "
              "that line is: "
              "<RLc>,<RLu>,<max_threshold>,"
              "<dedup_percentage_based_on_file_counts>,"
              "<dedup_percentage_based_on_bytes>")
    )

    simulate(parser.parse_args())
