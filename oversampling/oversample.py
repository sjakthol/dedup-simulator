import gzip
import numpy as np
from SMOTE import SMOTE
import itertools
import random

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

def formatNumber(v):
    if v < 1000:
        return "%i" % v
    elif v < 1000000:
        return "%ik" % (v / 1000)
    else:
        return "%iM" % (v / 1000000)

hashes = set()
samples = []
print("Reading samples.")
with gzip.open("niksula-file-data.txt.gz") as fd:
    for line in fd:
        hsh, count, size = line.decode("UTF-8").split("  ")
        hashes.add(int(hsh, 16))
        samples.append([int(count), int(size)])

print("Samples read. Reading already generated hashes")
with gzip.open("niksula-file-data-synthetic.txt.gz") as fd:
    for line in fd:
        hsh = line.decode("UTF-8").split("  ")[0]
        hashes.add(int(hsh, 16))

print("Input read. Converting it to NumPy array")
np_samples = np.array(samples, np.int32)
print("np.array finished")

N = 700
k = 5
smote = SMOTE(np_samples,N,k=k)
synth = smote.over_sampling()
print('# Synth Samps: ', synth.shape[0])

with gzip.open("niksula-file-data-synthetic-1.txt.gz", 'w') as fd:
    for (i, sample) in enumerate(synth):
        hsh = random.getrandbits(160)
        while hsh in hashes:
            hsh = random.getrandbits(160)

        hashes.add(hsh)

        fd.write(("%040x  %i  %i\n" % (hsh, int(sample[0]), int(sample[1]))).encode("UTF-8"))
        if i % 100000 == 0:
            print("%s samples outputted" % formatNumber(i))
