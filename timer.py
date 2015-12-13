import time

try:
    # Python >= 3.3
    timestamp = time.perf_counter
except AttributeError as e:
    # Python < 3.3
    timestamp = time.clock


class Timer:
    """A simple timer class."""
    def __init__(self):
        self.reset()

    def reset(self):
        """Resets the epoch of the timer."""
        self._stamp = timestamp()

    @property
    def elapsed(self):
        """The seconds since the timer last reset or initialized."""
        return timestamp() - self._stamp

    @property
    def elapsed_str(self):
        """A human readable version of @property elapsed."""
        diff = self.elapsed
        for unit in ["s", "ms", "µs"]:
            if diff < 1:
                diff *= 1000
                continue

            return "%3.1f%s" % (diff, unit)
        return "%3.1f%s" % (diff, "ns")
