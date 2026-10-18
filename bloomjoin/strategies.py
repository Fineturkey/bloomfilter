"""Extension points for Bloom filtering and cost-selected sizing."""


class BloomFilter:
    def __init__(self, bit_count, hash_count):
        raise NotImplementedError("TODO: packed bits and stable compatible hashes")

    def add(self, key):
        raise NotImplementedError

    def might_contain(self, key):
        raise NotImplementedError

    def intersection(self, other):
        raise NotImplementedError


def choose_filter_size(local_count, remote_count, record_width):
    raise NotImplementedError("TODO: implement and document the paper's cost model")
