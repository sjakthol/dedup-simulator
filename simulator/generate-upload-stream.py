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
import fileinput
import functools
import hashlib
import itertools
import math
import operator
import random
import sys
import tqdm
import timer
import utils

# Program description
DESC = ("Generates an upload request stream for the simulator to consume. The "
        "data should be provided in the form of file_counts.py output "
        "('<sha1 hash>  <copies>  <size>')")


class UploadStreamGenerator:

    File = collections.namedtuple("File", "hash, count, size")

    def __init__(self, args):
        self.args = args

    @utils.timeit
    def generate(self):
        # Read the input
        files = self.read_input()
        total_uploads = self.count_uploads(files)
        print("+++ Input generated: uploads=%i, files=%i" % (
            total_uploads, len(files)
        ), file=sys.stderr)

        # Generate the uploads
        uploads = self.compute_uploads(files)

        # Output them
        self.output_uploads(uploads, total_uploads)

    def get_generator(self):
        """A function that creates a function that generates random numbers
        from a specific distribution to a single file. The numbers generated by
        the function will be the time ticks the file is uploaded during the
        simulation.

        Return:
            A function that returns an integer.
        """

        raise NotImplementedError("Implement get_generator()!")

    @utils.timeit
    def read_input(self):
        """Reads the input data from source given in arguments.

        Returns:
            A list of (hash, count, size) tuples.
        """

        print("+++ Reading data from %s" % self.args.input, file=sys.stderr)

        def convert(tokens):
            """A helper that converts tokens on a line to integers."""
            return (
                int(tokens[0], 16),
                int(tokens[1]),
                int(tokens[2]))

        with fileinput.input(self.args.input) as lines:
            # Tokenize the lines on two spaces
            tokenised = map(lambda line: line.split("  "), lines)

            # Parse the tokenized data
            data = map(convert, tokenised)

            # Collect the data to a list since he file is closed when we leave
            # this with block
            return utils.collect(data)

    @utils.timeit
    def count_uploads(self, files):
        """Counts the total number of uploads the read dataset contains.

        Args:
            files - The list of files read_input() returned.

        Returns:
            The number of uploads.
        """

        return functools.reduce(lambda count, file: count + file[1], files, 0)

    @utils.timeit
    def compute_uploads(self, files):
        """Computes the time ticks each upload happens at.

        Args:
            files - The list of files read_input() returned.

        Returns:
            A dict time -> uploads containing uploads for each time tick. Each
            key is a distinct time tick and each value is a list of
            (hash, size) tuples.
        """

        print("+++ Computing uploads", file=sys.stderr)

        uploads = {}
        for hash, count, size in tqdm.tqdm(files):
            generator = self.get_generator()

            for _ in range(0, count):
                uploads.setdefault(int(round(generator())), []) \
                    .append((hash, size))

        return uploads

    @utils.timeit
    def output_uploads(self, uploads, total_uploads=None):
        """Outputs the uploads generated by compute_uploads().

        Args:
            uploads - The uploads generated by compute_uploads().
            total_uploads - The total number of uploads in the stream. Used for
                progress reporting (optional)
        """

        print("+++ Outputting uploads", file=sys.stderr)

        # Sort the uploads in the order sorted by their keys
        stream = sorted(uploads.items(), key=operator.itemgetter(0))

        # Only take the values which are lists of uploads
        stream = map(operator.itemgetter(1), stream)

        # Shuffle the uploads for each time tick
        stream = map(utils.shuffle, stream)

        # Chain the lists together into a single iterator
        stream = itertools.chain.from_iterable(stream)

        digest = hashlib.sha256()

        for hash, size in tqdm.tqdm(stream, total=total_uploads):
            # The uploads are packed into 25 bytes: 20 bytes for the hash
            # and 5 bytes for the file size
            upload = hash | size << 160
            encoded = upload.to_bytes(utils.BYTES_PER_UPLOAD,
                                      byteorder="big")

            digest.update(encoded)
            sys.stdout.buffer.write(encoded)

        print("+++ Upload stream outputted. SHA-256: %s" % (
            digest.hexdigest()
        ), file=sys.stderr)


class UniformStreamGenerator(UploadStreamGenerator):
    def __init__(self, args):
        super().__init__(args)

    def generator(self):
        return 1

    def get_generator(self):
        return self.generator


class NormalStreamGenerator(UploadStreamGenerator):
    def __init__(self, args):
        super().__init__(args)

    def get_generator(self):
        mu = random.randint(1, 20000)
        sigma = random.randint(20, 2000)

        return functools.partial(random.gauss, mu, sigma)


class LogNormalStreamGenerator(UploadStreamGenerator):
    def __init__(self, args):
        super().__init__(args)

    def get_generator(self):
        mu = math.log(random.randint(1, 20000))
        sigma = math.log(random.randint(20, 2000))

        return functools.partial(random.lognormvariate, mu, sigma)


@utils.timeit
def main():
    parser = argparse.ArgumentParser(description=DESC)
    parser.add_argument("input",
                        action="store", default="-", type=str, nargs="?",
                        help="The input file to read the popularity data " +
                             "from. Each line in the source must have form " +
                             "'<sha1 hash>  <copies>  <size>'. Defaults to " +
                             "stdin '-'")
    parser.add_argument("--distribution",
                        action="store", choices=["uniform", "normal", "lognormal"],
                        default="uniform",
                        help="The type of distribution the popularities " +
                             "follow wrt. to time")
    args = parser.parse_args()

    if args.distribution == "uniform":
        g = UniformStreamGenerator(args)
    elif args.distribution == "normal":
        g = NormalStreamGenerator(args)
    elif args.distribution == "lognormal":
        g = LogNormalStreamGenerator(args)

    g.generate()


if __name__ == "__main__":
    sys.exit(main())
