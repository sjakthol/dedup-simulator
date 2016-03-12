A simulator and related scripts for measuring efficiency of an encrypted data
deduplication solution.

* [Introduction](#introduction)
* [Setup](#setup)
* [Dataset Collector](#dataset-collector)
* [Upload Request Stream Generator](#upload-request-stream-generator)
* [Simulator](#simulator)
* [Perfect Protocol Simulator](#perfect-protocol-simulator)
* [Links](#links)

## Introduction
This repository contains various components that can be used to measure the
efficiency of a deduplication protocol. These components are:
* Dataset Collector - Collects file size and popularity data from UNIX systems.
* Upload Request Stream Generator - Generates a stream of upload requests from
the collected datasets.
* Simulator - Reads the generated upload request stream and simulates the
deduplication protocol.

Together these tool form a simulator pipeline where the output of the previous
tool is the input for the next step.

This repository also contains additional tools that might be useful:
* Perfect Protocol Simulator - Measures the perfect deduplication percentage
for the generated upload request streams that provides a baseline for
comparisons.
* Oversampler - A tool for generating larger datasets from a collected dataset.

The usage of these tools is described in the chapters below.

## Setup
Before the simulator can be used, you need to setup python3 and a virtual
environment for the required dependencies. The simulator has been used with
python 3.4.3 but it should also work with newer python3 releases.

To install the required dependencies, run the following commands:
```shell
python3 -m venv venv            # Create virtualenv to the venv/ directory
source venv/bin/activate        # Activate the virtualenv
pip install -r requirements.txt # Install the dependencies
```

**Note:** If you want to use the oversampler, a bunch of extra dependencies
are required. See the oversampler documentation below for instructions.

### Dataset Collector
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

#### Usage Examples
```
# Collect data from the entire file system and write the results to
# |root-data.txt| in the current directory
python ./scripts/file_counts.py / > root-data.txt

# Collect data from user home directories and write the data to |home-data.txt|
python ./scripts/file_counts.py /home > home-data.txt
```

**Important**: This script requires __python2__ instead of python3 to support
larger number of unix systems. Python2 can be installed from the python
website. Therefore, it should not be executed in the virtualenv created in
the setup section

### Upload Request Stream Generator
One the data has been collected the data needs to be turned into a list of
upload requests. The `simulator/generate-upload-stream.py` script does just
that.

It reads the dataset from given file (standard input by default) and turns it
into a binary stream of upload requests that consists of the file size (5
bytes) and hash (20 bytes).

The uploads of a file with respect to time in the stream follow either uniform,
normal or log-normal distributions. Basically, you specify the distribution to
use and each upload is assigned an upload time _t_ where _t_ is drawn from the
specified distribution with parameters randomly chosen for that particular
file. The uploads are then sorted by the upload times and outputted in that
order (in case multiple uploads have the same upload time t, those uploads are
randomly ordered).

The parameter limits for the supported distributions are (ln = natural log):
* normal: `1 < mean < 20000` and `20 < standard deviation < 2000`
* log-normal: `ln(1) < mean < ln(20000)` and `ln(20) < standard deviation <
ln(2000)`

**Note**: If you wish to change these limits, you need to change the code. They
are generated in the get_generator() function of different distribution
classes.

#### Usage Examples
```shell
# uniform distribution; data from home-data.txt
python3 ./simulator/generate-upload-stream.py home-data.txt > home-uniform-stream.bin

# normal distribution; data from stdin
cat home-data.txt | python3 ./simulator/generate-upload-stream.py --distribution=normal > home-normal-stream.bin

# log-normal distribution; data from stdin
cat home-data.txt | python3 ./simulator/generate-upload-stream.py --distribution=lognormal > home-lognormal-stream.bin
```

### Simulator
The simulator reads an upload request stream from the standard input and prints
the results to the standard output. It has a lot of command-line options that
modify the protocol, the protocol parameters and output formats. These options
are documented here and also when passing the simulator a `--help` flag.

#### Protocol Options
These options can be specified in the command line to modify the actual
protocol used for the simulation:
* `--with-sizes` - take file sizes into account when performing deduplication
* `--deduplicate-below-threshold` - also perform deduplication if the random
threshold for a file has not been met (server side deduplication)
* `--one-successful-check` - a checker stops performing checks once it has
performed one successful check

__Note__: By default, the simulator implements a franken-version of the
protocol that has never really been used. So you want to specify at least one
options shown above.

#### Protocol Parameters
The following options modify the protocol parameters:
* `--short-hash-length` - (int) the length of short hash in bits (default: 13)
* `--hash-length` - (int) the length of the dataset hashes in bits (default:
160)
* `--check-limit` - (int) the number of times an uploader can perform a check
for a file (default: 70)
* `--pake-runs` - (int) the number of files considered for deduplication for
each upload (default: 30)
* `--max-threshold` - (int) the maximum value for the random threshold
(default: 20)
* `--offline-rate` - (float in range [0, 1]) the probability that a checker is
offline during an upload (default: 0 i.e. always online)

#### Output Format
By default, the simulator prints the simulation status after each upload as a
comma separated list of values that contains statistics about the number of
files and bytes that have been uploaded and stored up to that point. Each line
has following format:
```
<files_in_storage>,<files_uploaded>,<data_in_storage>,<data_uploaded>
```

This data can be used to compute the deduplication percentages with both file
counts (use the first two columns) and file sizes (use last two columns). When
the data is redirected to a file, the result will be a valid CSV file with raw
data from the simulations.

However, if you do not care about the intermediate state but only want the
DDP at the end of the simulation, specify the `--only-final` flag. This will
suppress the intermediate results and print a single line at the end of the
simulation that contains the protocol parameters and final DDPs:
```
<RLc>,<RLu>,<max_threshold>,<offline_rate>,<dedup_percentage_based_on_file_counts>,<dedup_percentage_based_on_bytes>
```

__Note__: The simulator also reports progress to stderr by default.

#### Usage Examples
```shell
# Processes the uploads from home-stream.bin, the protocol uses file sizes
# when selecting deduplication candidates and performs deduplication even below
# threshold and each checker stops performing checks once a match is found.
# Default parameters are used and results.csv contains statistics after every
# upload (format above).
cat home-uniform-stream.bin | python3 simulator/simulator.py --with-sizes --deduplicate-below-threshold --one-successful-check > results.csv

# Simulation with RLu = 40, RLc = 60 (output as above) but only to terminal
cat home-uniform-stream.bin | python3 ./simulator/simulator.py --pake-runs 40 --check-limit 60

# Same as the first one, but only store 10000 samples evenly along the
# simulation (by default a lot of data is outputted and this is enough to
# visualize the evolution). resamp is installed among the requirements.
cat home-uniform-stream.bin | python3 simulator/simulator.py --with-sizes --deduplicate-below-threshold --one-successful-check | resamp -k 10000 | sort -n > result-samples.csv

# Simulation that only prints final result to final-result.csv (see format
# above):
cat home-uniform-stream.bin | python3 ./simulator/simulator.py --only-final > final-result.csv
```

#### Advanced Example
Here's a few examples that use [GNU Parallel](http://www.gnu.org/s/parallel) to
perform the simulations with different parameters. We start by generating
differently distributed streams, test out different rate limits for the streams
and run the simulations with different offline rates (default rate limits).

Here we assume that the directory structure is the following:
```
├── datasets
│   ├── (empty directory)
├── dedup-simulator
│   ├── (the simulator code; should be the working directory)
├── results
│   ├── (empty directory)
├── media-file-data.txt.gz
└── enterprise-file-data.txt.gz
```

Here `{media, enterprise}-file-data.txt.gz` contains two datasets in the
dataset collector format.

##### 1. Generate upload request streams
The following command generates three upload request streams (uniform, normal,
lognormal) for both datasets (media, enterprise):
```
parallel --progress --jobs 4 'zcat ../{1}-file-data.txt.gz | ./simulator/generate-upload-stream.py --distribution {2} | gzip > ../datasets/{1}-{2}-stream.bin.gz' ::: media enterprise ::: uniform normal lognormal
```

After the command finishes, you should have 6 streams in the datasets folder:
```
├── datasets
│   ├── enterprise-lognormal-stream.bin.gz
│   ├── enterprise-normal-stream.bin.gz
│   ├── enterprise-uniform-stream.bin.gz
│   ├── media-lognormal-stream.bin.gz
│   ├── media-normal-stream.bin.gz
│   └── media-uniform-stream.bin.gz
```

##### 2. Simulate different rate limits
The following command takes all six upload request streams generated in the
previous step and for all of them, simulates different rate limit combinations:
```
parallel --progress --jobs 4 'zcat ../datasets/{1}-{2}-stream.bin.gz | ./simulator/simulator.py --deduplicate-below-threshold --one-successful-check --with-sizes --only-final --check-limit {3} --pake-runs $(echo "100-{3}" | bc) --only-final >> ../results/{1}-{2}-rate-limits.csv' ::: media enterprise ::: uniform normal lognormal ::: $(seq 10 10 90)
```

After the command finishes, you have the following files in the results directory:
```
├── results
│   ├── enterprise-lognormal-rate-limits.csv
│   ├── enterprise-normal-rate-limits.csv
│   ├── enterprise-uniform-rate-limits.csv
│   ├── media-lognormal-rate-limits.csv
│   ├── media-normal-rate-limits.csv
│   └── media-uniform-rate-limits.csv
```

Each file contains results from simulations with different rate limit (format
as documented above for the `--only-final` flag):
```
30,70,20,0,0.9731817809066805,0.9731817809066805
40,60,20,0,0.9736812677522844,0.9736812677522844
...
```

##### 3. Simulate the protocol with different offline rates
The following command tests different offline rates for all 6 streams using
fixed rate limits (for clarity they are explicitly passed to the command)
```
parallel --progress --jobs 4 'zcat ../datasets/{1}-{2}-stream.bin.gz | ./simulator/simulator.py --deduplicate-below-threshold --one-successful-check --only-final --check-limit 70 --pake-runs 30 --offline-rate {3} >> ../results/{1}-{2}-offline-rates.csv' ::: media enterprise ::: uniform normal lognormal ::: $(LANG=C seq 0.1 0.1 0.9)
```

As in the previous step, this command runs the simulation with different
offline rates for all datasets and produces following output files:
```
├── results
│   ├── enterprise-lognormal-offline-rates.csv
│   ├── enterprise-normal-offline-rates.csv
│   ├── enterprise-uniform-offline-rates.csv
│   ├── media-lognormal-offline-rates.csv
│   ├── media-normal-offline-rates.csv
│   ├── media-uniform-offline-rates.csv
```

They have the same format as above.

##### 4. Measure the evolution of DDP
The following command measures the evolution of DDP during the simulation
(notice that `--only-final` is not used here) with fixed rate limits and
offline rate. The output files contain 10000 samples distributed evenly among
the simulation:
```
parallel --progress --jobs 4 'zcat ../datasets/{1}-{2}-stream.bin.gz | ./simulator/simulator.py --deduplicate-below-threshold --one-successful-check --with-sizes --check-limit 70 --pake-runs 30 --offline-rate 0.3 | resamp -k 10000 | sort -n | gzip > ../results/{1}-{2}-evolution.csv.gz' ::: media enterprise ::: uniform normal lognormal
```

The command produces the following output files:
```
├── results
│   ├── enterprise-lognormal-evolution.csv.gz
│   ├── enterprise-normal-evolution.csv.gz
│   ├── enterprise-uniform-evolution.csv.gz
│   ├── media-lognormal-evolution.csv.gz
│   ├── media-normal-evolution.csv.gz
│   ├── media-uniform-evolution.csv.gz
```

Each line contains stats about uploaded and stored files and bytes that can be
used to calculate the DDP (see above for column order).


## Perfect Protocol Simulator
TODO

## Links
* Paper: https://eprint.iacr.org/2015/455.pdf
* Demo Implementation: https://git.ssg.aalto.fi/close/cloud-dedup
