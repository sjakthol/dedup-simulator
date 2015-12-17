A simulator and related scripts for measuring efficiency of an encrypted data
deduplication solution.

* [Links](#)
* [Usage](#)
  * [Collecting a dataset](#)
  * [Generate an upload request stream](#)
  * [Perform the simulation](#)
* [Scripts](#)
  * [Sampler](#)
  * [Short hash and size listing](#)

## Links
* Paper: https://eprint.iacr.org/2015/455.pdf
* Demo Implementation: https://git.ssg.aalto.fi/close/cloud-dedup



## Usage

The basic steps for performing a simulation are the following:
* Execute `scripts/file_counts.py` to collect file popularity and size
information for the simulations (needs to be done once)
* Generate an upload request stream with `simulator/upload-request-stream.py`
(once per dataset / generation scheme)
* Run the simulation with `simulator/simulator.py`

All together:
```shell
python scripts/file_counts.py | python3 simulator/upload-request-stream.py |
python3 simulator/simulator.py > results.csv
```

### Collecting a dataset
The `scripts/file_counts.py` is used to collect the dataset for performing the
simulations. Given a directory, the script hashes all the files under that
directory and for each unique file discovered the following information is
printed to standard output:
* Hex-encoded SHA-1 hash of the file
* The number of copies found for that file
* The size of the file (bytes)

The standard output should be redirected to a file. Each output line contains
information for a single file with each value separated by two spaces:
```
  <hash>  <copies>  <size>
```

__Note__: Unlike other programs in this repository, this is a python2 program.

#### Example
To collect data from all home directories, execute
```shell
python file_counts.py /home > home-data.txt
```

The data will be found from the `home-data.txt` file.

### Generate an upload request stream
One the data has been collected the data needs to be turned into a list of
upload requests. The `simulator/upload-request-stream.py` script does just that.
It reads the dataset from given file (standard input by default) and turns it
into a binary stream of upload requests that consists of the file size (5
bytes) and hash (20 bytes).

#### Example
Generate an upload request stream where each upload is evenly distributed over
the stream:
```
cat home-data.txt | python3 simulator/upload-request-stream.py > home-stream.bin
```

The file `home-stream.bin` will contain the binary packed upload requests.

### Perform the simulation
Now that you have an upload request stream, you can feed it to the simulator.
The simulator simulates each upload request and prints two values after each
(separated by commas):
* total size of the files in the storage
* total size of the files in the upload stream so far

These values can be used to calculate the deduplication percentage.

__Note__: The simulator implements a couple of versions in the protocol (the
original and one currently in development). The development version can be
specified with the `--with-sizes` option.

#### Example
Simulate the uploads of the stream generated in previous process:
```
cat home-stream.bin | python3 simulator/simulator.py > results.csv
```

The results can be found from the `results.csv` file.

## Scripts
The scripts folder contains a couple useful scripts.

### Sampler
Given a number of samples and the number of all lines to be fed to the script,
the `scripts/sampler.py` will select evenly generated line samples that it
prints to standard output. The first and last line are always included.

The output lines will be prepended with the line number and a comma.

#### Example: Print 10,000 lines from 110,231,310 total lines
Here the file `data` contains 110,231,310 lines:
```shell
cat data | python3 scripts/sampler.py --samples 10000 --total-lines 110231310 >
samples
```

The `samples` file contains following data:
```
<sample 1 line number>, <sample 1>
<sample 2 line number>, <sample 2>
...
<sample 10000 line number>, <sample 10000>
```

### Short hash and size listing
The scripts `list-sh-size-pairs.py` and `list-sh.py` will take a data file
generated with `file_counts.py` and print the (short hash, file size) pairs
(first script) or short hashes (second script) to the standard output.
