# Author: Dave Rivera <daverivera90@gmail.com>
#         Julian David Arias Londoño  <jdarias@udea.edu.co>

from sklearn.neighbors import NearestNeighbors
import numpy as np
import time

try:
    timestamp = time.perf_counter
except AttributeError as e:
    timestamp = time.clock


def formatNumber(v):
    if v < 1000:
        return "%i" % v
    elif v < 1000000:
        return "%ik" % (v / 1000)
    else:
        return "%iM" % (v / 1000000)


class SMOTE():
    """SMOTE: Oversampling the minority class."""

    def __init__(self, samples, N=10, k=5):
        self.n_samps, self.n_attrs = samples.shape
        self.N = N
        self.k = k
        self.samples = samples

    def over_sampling(self):
        """ Generates syntethic samples

        Parameters
        ----------
        T: array-like, shape = [n_samps, n_attrs]
            Minority class Samples

        N:
            Amount of SMOTE N%. Percentage of new syntethic samples

        k: int, optional (default = 5)
            Number of neighbors to use by default for k_neighbors queries.

        Returns
        -------
        syntethic: array, shape = [(N/100) * T]
            Syntethic minority class samples

        Examples
        --------

        See also
        --------

        Notes
        -----
        """

        # If N is less than 100%, randomize the monority class samples as
        # only a random percent of them will be SMOTEd.
        self.n_synth = int((self.N/100)*self.n_samps)

        # Randomize minority class samples
        rand_indexes = np.random.permutation(self.n_samps)
        if self.N > 100:
            self.N = int(np.ceil(self.N/100))
            for i in range(self.N-1):
                values = np.random.permutation(self.n_samps)
                rand_indexes = np.append(rand_indexes, values)

        self.syntethic = np.zeros((self.n_synth, self.n_attrs))
        self.newindex = 0

        print("Computing nearest neighbors")
        s = timestamp()
        nearest_k = NearestNeighbors(n_neighbors=self.k).fit(self.samples)
        print("Computed nearest neighbors [%is]" % (timestamp() - s))

        s = timestamp()
        k = 0
        # for i in range (0, self.n_samps-1):
        for i in rand_indexes[:self.n_synth]:
            nnarray = nearest_k.kneighbors(self.samples[i],
                                           return_distance=False)[0]
            self.__populate(i, nnarray)
            k += 1
            if k % 1000000 == 0:
                print("[%is] %s samples created" % (timestamp() - s,
                      formatNumber(k)))

        return self.syntethic

    def __populate(self, i, nnarray):
        ## Choose a random number between 0 and k
        nn = np.random.randint(0, self.k)
        while nnarray[nn] == i:
            nn = np.random.randint(0, self.k)

        dif = self.samples[nnarray[nn]] - self.samples[i]
        gap = np.random.rand(1, self.n_attrs)

        self.syntethic[self.newindex] = self.samples[i] + gap.flatten() * dif
        self.newindex += 1
