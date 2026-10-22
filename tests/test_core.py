import unittest

from simple_interval_merge.core import (
    Interval,
    merge,
    subtract,
    intersect,
    complement,
)


class TestMerge(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(merge([]), [])

    def test_single(self):
        self.assertEqual(merge([(1, 5)]), [Interval(1, 5)])

    def test_disjoint_sorted(self):
        self.assertEqual(
            merge([(1, 3), (5, 7)]),
            [Interval(1, 3), Interval(5, 7)],
        )

    def test_disjoint_unsorted(self):
        self.assertEqual(
            merge([(5, 7), (1, 3)]),
            [Interval(1, 3), Interval(5, 7)],
        )

    def test_adjacent_merge(self):
        self.assertEqual(merge([(1, 3), (3, 5)]), [Interval(1, 5)])

    def test_overlapping(self):
        self.assertEqual(merge([(1, 5), (3, 7)]), [Interval(1, 7)])

    def test_nested_dropped(self):
        self.assertEqual(merge([(1, 10), (3, 5)]), [Interval(1, 10)])

    def test_zero_width_dropped(self):
        self.assertEqual(merge([(1, 1), (2, 5)]), [Interval(2, 5)])

    def test_unsorted_mess(self):
        self.assertEqual(
            merge([(10, 12), (1, 4), (5, 9), (3, 6), (20, 25)]),
            [Interval(1, 9), Interval(10, 12), Interval(20, 25)],
        )

    def test_invalid_order_raises(self):
        with self.assertRaises(ValueError):
            merge([(5, 1)])


class TestComplement(unittest.TestCase):
    def test_empty_universe_full(self):
        self.assertEqual(complement([], Interval(0, 10)), [Interval(0, 10)])

    def test_exact_cover(self):
        self.assertEqual(complement([(0, 10)], Interval(0, 10)), [])

    def test_middle_hole(self):
        self.assertEqual(
            complement([(3, 7)], Interval(0, 10)),
            [Interval(0, 3), Interval(7, 10)],
        )

    def test_adjacent_pieces(self):
        self.assertEqual(
            complement([(0, 3), (3, 7)], Interval(0, 10)),
            [Interval(7, 10)],
        )

    def test_clamps_to_universe(self):
        self.assertEqual(complement([(-100, 200)], Interval(0, 10)), [])


class TestIntersect(unittest.TestCase):
    def test_disjoint_sets(self):
        self.assertEqual(intersect([(0, 2)], [(5, 8)]), [])

    def test_partial_overlap(self):
        self.assertEqual(
            intersect([(1, 5)], [(3, 7)]),
            [Interval(3, 5)],
        )

    def test_one_inside_other(self):
        self.assertEqual(
            intersect([(0, 10)], [(3, 5)]),
            [Interval(3, 5)],
        )

    def test_multiple_pieces(self):
        self.assertEqual(
            intersect([(0, 4), (6, 10)], [(2, 8)]),
            [Interval(2, 4), Interval(6, 8)],
        )

    def test_no_overlap_at_boundary(self):
        self.assertEqual(intersect([(0, 3)], [(3, 5)]), [])

    def test_empty_input(self):
        self.assertEqual(intersect([], [(0, 5)]), [])
        self.assertEqual(intersect([(0, 5)], []), [])


class TestSubtract(unittest.TestCase):
    def test_disjoint_unchanged(self):
        self.assertEqual(
            subtract([(0, 5)], [(10, 15)], Interval(0, 20)),
            [Interval(0, 5)],
        )

    def test_middle_removed(self):
        self.assertEqual(
            subtract([(0, 10)], [(3, 7)], Interval(0, 10)),
            [Interval(0, 3), Interval(7, 10)],
        )

    def test_boundary_touch(self):
        self.assertEqual(
            subtract([(0, 10)], [(5, 10)], Interval(0, 10)),
            [Interval(0, 5)],
        )

    def test_all_removed(self):
        self.assertEqual(
            subtract([(0, 5)], [(0, 5)], Interval(0, 10)),
            [],
        )

    def test_multiple_subtractions(self):
        self.assertEqual(
            subtract([(0, 10)], [(2, 3), (5, 6)], Interval(0, 10)),
            [Interval(0, 2), Interval(3, 5), Interval(6, 10)],
        )

    def test_universe_bounds_result(self):
        # The result never extends beyond universe, even when A does.
        self.assertEqual(
            subtract([(-5, 15)], [(0, 5)], Interval(0, 10)),
            [Interval(5, 10)],
        )


class TestIntervalType(unittest.TestCase):
    def test_namedtuple_fields(self):
        iv = Interval(1, 2)
        self.assertEqual(iv.start, 1)
        self.assertEqual(iv.end, 2)
        self.assertEqual(iv[0], 1)
        self.assertEqual(iv[1], 2)

    def test_accepts_plain_tuples(self):
        self.assertEqual(merge([(1, 2), (2, 3)]), [Interval(1, 3)])

    def test_accepts_interval_objects(self):
        self.assertEqual(merge([Interval(1, 2), Interval(2, 3)]), [Interval(1, 3)])

    def test_rejects_bad_pair(self):
        with self.assertRaises(TypeError):
            merge([(1, 2, 3)])


if __name__ == "__main__":
    unittest.main()
