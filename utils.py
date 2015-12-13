import cProfile
import functools
import random
import resource
import timer
import sys

REPORT_FREQUENCY = 500000

# 20 bytes for the SHA1 hash, 5 bytes for the file size.
BYTES_PER_UPLOAD = 25


def timeit(fn):
    """Decorator that measures how long a function call takes and prints it to
       stderr.
    """

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        time = timer.Timer()
        rval = fn(*args, **kwargs)
        print("--- %s(): %s." % (fn.__name__, time.elapsed_str),
              file=sys.stderr)
        return rval

    return wrapper


def profileit(func):
    """A decorator that will record and print a cProfile profile for the
       decorated function.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        profiler = cProfile.Profile()
        profiler.enable()
        rval = func(*args, **kwargs)
        profiler.disable()
        try:
            # Only in 3.3
            profiler.print_stats(sort="cumtime")
        except KeyError:
            profiler.print_stats()
        return rval

    return wrapper


def num_fmt(num, suffix=''):
    """Formats a size string."""
    for unit in ['', 'k', 'M', 'G', 'T', 'P', 'E', 'Z']:
        if abs(num) < 1000:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1000
    return "%.1f%s%s" % (num, 'Y', suffix)


def sizeof_fmt(num, suffix='B'):
    """Formats a size string."""
    for unit in ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Y', suffix)


def get_memory_usage():
    """Fetches the resource usage of the process."""
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss


def get_size(obj):
    """Fetches the size of an object."""
    return sys.getsizeof(obj, -1)


def get_mem_info(obj=None):
    """Get a string that contains the size of object and total memory usage."""
    totalmem = sizeof_fmt(get_memory_usage() * 1024)
    if not obj:
        return "total=%s" % totalmem

    datamem = sizeof_fmt(get_size(obj))
    return "obj=%s, total=%s" % (datamem, totalmem)


def shuffle(in_list):
    """A generator that iterates the list in random order.

    Arguments:
    in_list -- The list to iterate. The generator will modify this list.
    """

    # Fisher-Yates shuffle
    for i in range(len(in_list) - 1, 0, -1):
        rnd = random.randint(0, i)
        # Swap the ith element with the rndth one.
        in_list[i], in_list[rnd] = in_list[rnd], in_list[i]

        # Yield the rndth, now ith, element.
        yield in_list[i]

    # Yield the last element.
    yield in_list[0]


def read_upload_stream():
    """Reads the precomputed upload request stream from stdin. The stream MUST
       be generated with generate_upload_stream.py script.

       Yields:
          A (hash, size) tuple of each upload (int, int).
    """
    upload = sys.stdin.buffer.read(BYTES_PER_UPLOAD)
    while upload:
        data = int.from_bytes(upload, byteorder='big')
        hsh = data & 0xffffffffffffffffffffffffffffffffffffffff
        size = data >> 160

        # Yield the hash, size pair
        yield (hsh, size)

        # Read the next upload
        upload = sys.stdin.buffer.read(BYTES_PER_UPLOAD)
