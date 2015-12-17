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
import hashlib
import itertools
import sys
import timer
import utils

# Program description
DESC = ("Generates an upload request stream for the simulator to consume. The "
        "data should be provided in the form of file_counts.py output "
        "('<sha1 hash>  <copies>  <size>')")


@utils.timeit
def read_input(args):
    """Reads the input data from provided source

    Args:
        args: The command line arguments that contain input variable. The data
          will be read from this file.

    Returns:
        A iterator of file tupes of form (hash, count, size).

    Raises:
        Exception if the data can't be read from the input.
    """

    print("Reading data from %s" % args.input, file=sys.stderr)

    def convert(tokens):
        """A helper that converts tokens on a line to integers."""
        return (int(tokens[0], 16), int(tokens[1]), int(tokens[2]))

    with fileinput.input(args.input) as inpt:
        # The data needs to be collected in the with block or the file will be
        # closed before the lines are read
        lines = list(inpt)

        # Inner map tokenizes the lines, the outer converts the values to
        # integer triples
        return map(convert,
                   map(lambda line: line.split("  "), lines))


def print_uploads(uploads):
    """A method that prints uploads to stdout.

    Args:
        uploads: An iterator that yields (sha1 hash, size) pairs
    """

    # A hash that can be used to verify the result
    digest = hashlib.sha256()
    tmr = timer.Timer()
    for i, (hsh, size) in enumerate(uploads):
        if i and i % utils.REPORT_FREQUENCY == 0:
            print("%s uploads outputted, time %s, mem=[%s]" % (
                utils.num_fmt(i),
                tmr.elapsed_str,
                utils.get_mem_info()), file=sys.stderr)
            tmr.reset()

        try:
            # The uploads are packed into 25 bytes: 20 bytes for the hash and
            # 5 bytes for the file
            upload = hsh | size << 160
            encoded = upload.to_bytes(utils.BYTES_PER_UPLOAD, byteorder="big")
        except OverflowError:
            print("ERROR: hash | size << 160 did not fit into %i bytes" % (
                utils.BYTES_PER_UPLOAD), file=sys.stderr)
            raise

        digest.update(encoded)
        sys.stdout.buffer.write(encoded)

    print("Finished. SHA256 digest of the data: %s" % digest.hexdigest(),
          file=sys.stderr)


@utils.timeit
def collect(iter):
    """Collects values from iterator to list with progress reporting.

    Args:
        iter: The iterator to convert to list

    Returns:
        A List that contains the values from the iterable
    """

    lst = []
    tmr = timer.Timer()
    for i, value in enumerate(iter):
        if i and i % utils.REPORT_FREQUENCY == 0:
            print("%i items collected, time=%s, mem=[%s]" % (
                i, tmr.elapsed_str, utils.get_mem_info(lst)), file=sys.stderr)
            tmr.reset()

        lst.append(value)

    return lst


@utils.timeit
def generate_uniform_uploads(files, args):
    """Generates an upload request stream distributing the files uniformly.

    The uploads are printed to stdout.

    Args:
        files: Result of read_input()
        args: The command line arguments
    """

    print("Generating uploads with uniform distribution", file=sys.stderr)

    # Repeat each file based on their popularity
    stream = map(lambda f: itertools.repeat((f[0], f[2]), f[1]), files)

    # Flatten the nested iterators
    flat_stream = collect(itertools.chain.from_iterable(stream))

    # shuffle the uploads
    shuffled_stream = utils.shuffle(flat_stream)

    # Print them out
    print_uploads(shuffled_stream)


@utils.timeit
def main():
    parser = argparse.ArgumentParser(description=DESC)
    parser.add_argument("input",
                        action="store", default="-", type=str, nargs="?",
                        help="The input file to read the popularity data " +
                             "from. Each line in the source must have form " +
                             "'<sha1 hash>  <copies>  <size>'. Defaults to " +
                             "stdin '-'")
    parser.add_argument("--time-ticks",
                        action="store", default=100, type=int,
                        help="The number of time values in the simulation " +
                             "(ticks are integers 0, ..., --time-ticks.")
    parser.add_argument("--distribution",
                        action="store", choices=["uniform"], default="uniform",
                        help="The type of distribution the popularities " +
                             "follow wrt. to time")
    args = parser.parse_args()
    files = read_input(args)

    if args.distribution == "uniform":
        generate_uniform_uploads(files, args)


if __name__ == "__main__":
    sys.exit(main())
