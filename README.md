# simple-interval-merge

Merge, subtract and intersect sets of half-open intervals `[start, end)` using nothing but the Python standard library.

```python
from simple_interval_merge import Interval, merge, subtract, intersect, complement

# Merge overlapping and adjacent intervals.
merge([(1, 5), (3, 7), (10, 12)])
# -> [Interval(start=1, end=7), Interval(start=10, end=12)]

# Carve holes: subtract b from a within a fixed universe.
subtract([(0, 10)], [(3, 7)], Interval(0, 10))
# -> [Interval(start=0, end=3), Interval(start=7, end=10)]

# Intersect two sets of intervals.
intersect([(0, 4), (6, 10)], [(2, 8)])
# -> [Interval(start=2, end=4), Interval(start=6, end=8)]

# Complement of a set within a universe.
complement([(3, 7)], Interval(0, 10))
# -> [Interval(start=0, end=3), Interval(start=7, end=10)]
```

## Why this exists

Half-open intervals are the natural fit for range bookkeeping: `[1, 3)` and `[3, 5)` tile cleanly with no overlap and no gap, exactly like Python's `range` and slice syntax. This library gives you merge, subtract, intersect, and complement over sets of such intervals, returning results that are always sorted, disjoint, and free of zero-width intervals.

The one design decision you must know about: `subtract` takes a required `universe` argument. The complement of a half-open interval is otherwise unbounded on the side without a neighbour, so subtraction needs a finite frame to stay well-defined. Pick a universe wide enough to span everything `a` can cover; results are clamped to it.

## The awkward edge

Inputs may be plain `(start, end)` tuples or `Interval(start, end)` instances; both are accepted and treated identically. `start == end` is a valid zero-width interval and is silently dropped from results. `start > end` raises `ValueError` rather than being interpreted as an empty interval, because swapped bounds are almost always a caller bug.

## API

- `Interval(start, end)` — namedtuple with `.start` and `.end` fields.
- `merge(intervals)` — merge to a minimal disjoint sorted list.
- `complement(intervals, universe)` — `universe` minus the merged intervals.
- `intersect(a, b)` — overlap of two sets.
- `subtract(a, b, universe)` — `a` minus `b`, bounded by `universe`.

Run tests with `PYTHONPATH=src python -m unittest discover -s tests`.

## Design notes

The window stores values eagerly rather than keeping running aggregates. Running
sums drift with floating point over long streams, and recomputing from a small
buffer is cheap enough that the drift is not worth the speed.

