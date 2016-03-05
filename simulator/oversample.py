#!/usr/bin/env python3

import argparse
import fileinput
import numpy as np
import random
import smote
import sys
import tqdm
import utils

description = """
Create new synthetic uploads with SMOTE.

The program reads file data from the standard input where each line contains
the following information
  <hex-encoded hash>  <count>  <size>

and outputs new files with <count> and <size> generated using SMOTE with the
following format
  <hex-encoded hash>  <count>  <size>

The hashes are SHA1 and they are drawn from an uniform distribution.
"""


@utils.timeit
def read_input():
    """Read the input data from stdin.

    Returns:
        A tuple (hashes, samples) where hashes is a set of file hashes found
        from the stream and samples is an array of (count, size) pairs for
        the aforementioned hashes
    """
    hashes = set()
    samples = []

    files = 0
    uploads = 0

    for line in tqdm.tqdm(fileinput.input("-")):
        hsh, count, size = line.strip().split("  ")
        hsh, count, size = int(hsh, 16), int(count, 10), int(size, 10)
        files += 1
        uploads += count

        samples.append([count, size])
        hashes.add(hsh)

    assert len(samples) == len(hashes), "hash collisions!"

    print("+++ files=%i, uploads=%i" % (files, uploads), file=sys.stderr)

    return hashes, samples


@utils.timeit
def output_new_files(hashes, new_samples, args):
    """Prints new files from the SMOTEd samples.

    Params:
        hashes - the hashes found from the input data
        new_samples - the new samples generated with SMOTE
    """
    files = 0
    uploads = 0
    for sample in tqdm.tqdm(new_samples):
        hsh = random.getrandbits(args.hash_length)
        while hsh in hashes:
            # Like this will never happen
            hsh = random.getrandbits(args.hash_length)

        copies, size = int(sample[0]), int(sample[1])

        files += 1
        uploads += copies

        new_file = ("%040x  %i  %i\n" % (hsh, copies, size))
        sys.stdout.write(new_file)

    print("+++ files=%i, uploads=%i" % (files, uploads), file=sys.stderr)


@utils.timeit
def oversample(args):
    print("+++ Reading input", file=sys.stderr)
    hashes, samples = read_input()

    print("+++ Converting to numpy array", file=sys.stderr)
    np_samples = np.array(samples, np.int32)

    print("+++ Performing SMOTE", file=sys.stderr)
    new_samples = smote.SMOTE(np_samples, args.smote_amount, args.neighbors)

    print("+++ Outputting new files", file=sys.stderr)
    output_new_files(hashes, new_samples, args)


@utils.timeit
def main():
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "-k", "--neighbors", type=int, default=5,
        help="The number of nearest neighbors to use when performing SMOTE"
    )

    parser.add_argument(
        "-N", "--smote-amount", type=int,
        help=("The amount of SMOTE. Must be multiple of 100 where 100 means "
              "that for each input sample there will be one new sample")
    )

    parser.add_argument(
        "--hash-length", type=int, default=160,
        help=("The length of the file hashes to generate in bits. "
              "E.g. 160 for SHA1 or 256 for SHA256")
    )

    oversample(parser.parse_args())

if __name__ == "__main__":
    main()
