import unittest

from bloomjoin.strategies import choose_filter_size, MAX_FILTER_BITS


class CostSizingTests(unittest.TestCase):
    def test_paper_equal_cardinality_example(self):
        # Eq. (4): r=100, a=0, w2=256 bits gives 1001.617... bits.
        self.assertEqual(choose_filter_size(100, 100, 32), (1008, 7))
        self.assertEqual(choose_filter_size(100, 100, 32, selectivity=0.5), (864, 6))

    def test_cost_inputs_affect_size(self):
        baseline = choose_filter_size(100, 100, 32).bit_count
        self.assertGreater(choose_filter_size(100, 1000, 32).bit_count, baseline)
        self.assertGreater(choose_filter_size(100, 100, 128).bit_count, baseline)
        self.assertLess(choose_filter_size(100, 100, 32, selectivity=0.9).bit_count, baseline)

    def test_empty_and_no_benefit(self):
        for n, remote in ((0, 0), (0, 100), (100, 0)):
            self.assertEqual(choose_filter_size(n, remote, 32), (0, 0))
        self.assertEqual(choose_filter_size(100, 100, 32, selectivity=1), (0, 0))
        self.assertEqual(choose_filter_size(10000, 1, 1), (0, 0))

    def test_bounded_and_byte_aligned(self):
        for args in ((1, 10**1000, 1e300), (10**1000, 10**1000, 32), (1, 1, 1)):
            size = choose_filter_size(*args)
            self.assertLessEqual(size.bit_count, MAX_FILTER_BITS)
            self.assertEqual(size.bit_count % 8, 0)
            self.assertTrue(1 <= size.hash_count <= 32)

    def test_invalid_inputs_even_with_empty_table(self):
        for bad in (-1, 1.5, True, "10", None):
            with self.subTest(count=bad):
                with self.assertRaises(ValueError):
                    choose_filter_size(bad, 100, 32)
                with self.assertRaises(ValueError):
                    choose_filter_size(100, bad, 32)
        for width in (0, -1, float("nan"), float("inf"), True, "32", 10**1000):
            with self.subTest(width=width), self.assertRaises(ValueError):
                choose_filter_size(0, 100, width)
        for selectivity in (-0.1, 1.1, float("nan"), float("inf"), True, None):
            with self.subTest(selectivity=selectivity), self.assertRaises(ValueError):
                choose_filter_size(100, 100, 32, selectivity=selectivity)
