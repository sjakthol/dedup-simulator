#!/usr/bin/env python3

import fileinput
import hashlib
import sys
import timer
import utils

"""
Generates an upload request stream from the data collected by file_counts.py.
The input is read from stdin and the compact, binary output is written to
stdout.

Usage:
  cat <FILE_POPULARITY_DATA_FILE> | ./generate-upload-stream > <OUTPUT_FILE>

"""
# 20 bytes for the SHA1 hash, 5 bytes for the file size.
BYTES_PER_UPLOAD = 25

# The number of steps between printing reports during long lasting computation.
REPORT_FREQUENCY = 1000000


@utils.timeit
def read_input():
    with fileinput.input() as lines:
        uploads = []
        i = 0
        tmr = timer.Timer()

        for line in lines:
            hsh, count, size = line.split("  ")
            if "-" in size or "-" in count:
                continue

            uploads += [int(hsh, 16) | int(size) << 160] * int(count)
            i += 1
            if i % REPORT_FREQUENCY == 0:
                print("%s files, %s uploads, time %s, %s" % (
                    utils.num_fmt(i),
                    utils.num_fmt(len(uploads)),
                    tmr.elapsed_str,
                    utils.get_mem_info(uploads)), file=sys.stderr)
                tmr.reset()

        return uploads


@utils.timeit
def generate_uploads(uploads):
    i = 0
    digest = hashlib.sha256()
    tmr = timer.Timer()
    for upload in utils.shuffle(uploads):
        i += 1
        if i % REPORT_FREQUENCY == 0:
            print("%s uploads, time %s, %s" % (
                utils.num_fmt(i),
                tmr.elapsed_str,
                utils.get_mem_info()
            ), file=sys.stderr)
            tmr.reset()

        try:
            encoded = upload.to_bytes(BYTES_PER_UPLOAD, byteorder='big')
        except OverflowError as e:
            print("ERROR: size+hash does not fit into %i bytes" % (
                BYTES_PER_UPLOAD), file=sys.stderr)
            raise e

        digest.update(encoded)
        sys.stdout.buffer.write(encoded)

    print("Finished. SHA256 digest of the data: %s" % digest.hexdigest(),
          file=sys.stderr)


@utils.timeit
def main():
    uploads = read_input()
    generate_uploads(uploads)

if __name__ == "__main__":
    sys.exit(main())
