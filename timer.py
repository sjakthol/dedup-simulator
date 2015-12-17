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
