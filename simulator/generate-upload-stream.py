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
import random
import sys
import timer
import utils

# Program description
DESC = ("Generates an upload request stream for the simulator to consume. The "
        "data should be provided in the form of file_counts.py output "
        "('<sha1 hash>  <copies>  <size>')")


class UploadStreamGenerator:

    def __init__(self, args):
        self.args = args
        self.digest = hashlib.sha256()
        self.nuploads = 0

    def generate(self):
        self.files = self.read_input()
        self.total_uploads = self.count_uploads()

        print("Geneating a sequence of %i uploads (%i unique files)" % (
            self.total_uploads, len(self.files)
        ), file=sys.stderr)

        self.generate_uploads()
        print("Generated %i uploads" % self.nuploads, file=sys.stderr)

    def get_pdf(self):
        """A function that creates a function that gives the probability
        distribution for file over time.

        If the probability for a file is P(t) = x, then the file will be
        uploaded |x * copies| times during time t.

        Return:
            A function that takes one integer argument (time tick |t|) and
            returns the probability of the file being uploaded at the tick |t|.
        """

        raise NotImplementedError("Implement get_pdf()!")

    @utils.timeit
    def read_input(self):
        """Reads the input data from source given in arguments."""

        print("Reading data from %s" % self.args.input, file=sys.stderr)

        def convert(tokens):
            """A helper that converts tokens on a line to integers and creates
            a probability distribution over time for this file."""
            hsh = int(tokens[0], 16)
            count = int(tokens[1])
            return (
                hsh,
                count,
                int(tokens[2]),
                self.get_pdf(),
                count
            )

        with fileinput.input(self.args.input) as lines:
            # Tokenize the lines on two spaces
            tokenised = map(lambda line: line.split("  "), lines)

            # Parse the tokenized data
            data = map(convert, tokenised)

            # Collect the data to a list since he file is closed when we leave
            # this with block
            return utils.collect(data)

    def count_uploads(self):
        """Counts the total number of uploads the read dataset contains.

        Returns:
            The number of uploads.
        """
        return functools.reduce(lambda c, f: c + f[1], self.files, 0)

    def generate_uploads(self):
        """Generates the upload request stream."""
        # The time tick t
        t = 0

        tmr = timer.Timer()
        files = self.files
        while self.nuploads < self.total_uploads:
            # Files that still have uploads left for the next iteration
            next_files = []

            # The uploads triggered during this iteration
            uploads = []

            for hsh, total_copies, size, pdf, left in files:
                copies = int(math.ceil(pdf(t) * total_copies))
                copies = min(copies, left)

                # Append the uploads for this round
                uploads.append(itertools.repeat((hsh, size), copies))
                left -= copies

                # If there's still uploads left for the next rounds, add the
                # file back to the list
                if left > 0:
                    next_files.append((hsh, total_copies, size, pdf, left))

            # Dump the uploads for this tick
            all_ups = itertools.chain.from_iterable(uploads)
            self.output_uploads_for_tick(all_ups)

            print("t=%i, ups=%s, left=%i, time=%s, mem=[%s]" % (
                t,
                utils.num_fmt(self.nuploads),
                len(next_files),
                tmr.elapsed_str,
                utils.get_mem_info()
            ), file=sys.stderr)
            tmr.reset()

            if not files:
                break

            files = next_files
            t += 1

    def output_uploads_for_tick(self, uploads):
        """Outputs the uploads for given time tick.

        Args:
            uploads: An iterator that yields (sha1 hash, size) pairs

        Returns:
            True if at least one upload was outputted, false otherwise.
        """

        uploads = utils.collect(uploads)
        if not uploads:
            return False

        uploads = utils.shuffle(uploads)

        tmr = timer.Timer()
        for hsh, size in uploads:
            if self.nuploads and self.nuploads % utils.REPORT_FREQUENCY == 0:
                print("%s uploads outputted, time %s, mem=[%s]" % (
                    utils.num_fmt(self.nuploads),
                    tmr.elapsed_str,
                    utils.get_mem_info()), file=sys.stderr)
                tmr.reset()

            try:
                # The uploads are packed into 25 bytes: 20 bytes for the hash
                # and 5 bytes for the file
                upload = hsh | size << 160
                encoded = upload.to_bytes(utils.BYTES_PER_UPLOAD,
                                          byteorder="big")
            except OverflowError:
                print("ERROR: hash | size << 160 did not fit into %i bytes" % (
                    utils.BYTES_PER_UPLOAD), file=sys.stderr)
                raise

            self.nuploads += 1
            self.digest.update(encoded)
            sys.stdout.buffer.write(encoded)

        return True


class UniformStreamGenerator(UploadStreamGenerator):
    def __init__(self, args):
        super().__init__(args)

    def pdf(self, t):
        return 1 if not t else 0

    def get_pdf(self):
        return self.pdf


class NormalStreamGenerator(UploadStreamGenerator):
    sqrt2pi = math.sqrt(2 * math.pi)

    def __init__(self, args):
        super().__init__(args)

    def pdf(self, mu, sigma, t):
        return 1 / (sigma * self.sqrt2pi) * \
            math.exp(-(t - mu) * (t - mu) / (2 * sigma * sigma))

    def get_pdf(self):
        mu = random.randint(1, 2000)
        sigma = random.randint(20, 200)

        return functools.partial(self.pdf, mu, sigma)


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
                        action="store", choices=["uniform", "normal"],
                        default="uniform",
                        help="The type of distribution the popularities " +
                             "follow wrt. to time")
    args = parser.parse_args()

    if args.distribution == "uniform":
        g = UniformStreamGenerator(args)
    elif args.distribution == "normal":
        g = NormalStreamGenerator(args)

    g.generate()


if __name__ == "__main__":
    sys.exit(main())
