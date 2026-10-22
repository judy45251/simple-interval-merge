"""Core operations on sets of half-open intervals.

All intervals are half-open: [start, end). An interval [3, 7) contains 3, 4,
5, and 6, but not 7. This convention is taken from Python's built-in range and
slicing semantics; it makes adjacent intervals like [1,3) and [3,5) tile
without overlap or gaps.

Intervals are represented as Interval(start, end) namedtuples. All operations
return a list of Interval objects sorted by start, with no overlaps and no
zero-width intervals (start < end is the only way an interval survives).
"""

from collections import namedtuple
from typing import Iterable, List

# A namedtuple keeps intervals immutable, hashable, and indexable by position
# (interval[0], interval[1]) as well as by name (interval.start, interval.end).
# Returning a concrete type rather than a bare tuple makes the public API
# self-documenting at the cost of one extra class definition.
Interval = namedtuple("Interval", ["start", "end"])


def _validate(interval: Interval) -> None:
    """Raise on malformed intervals before they corrupt a computation.

    Half-open semantics mean start == end is legal (an empty interval) but
    we still reject start > end so callers fail loudly on swapped bounds
    rather than silently producing nonsense.
    """
    if interval.start > interval.end:
        raise ValueError(
            "interval start must be <= end; got %r > %r"
            % (interval.start, interval.end)
        )


def _normalise(intervals: Iterable) -> List[Interval]:
    """Coerce input to a clean list of validated Interval objects.

    Accepts both Interval instances and plain (start, end) tuples so callers
    don't have to wrap every pair by hand.
    """
    result: List[Interval] = []
    for item in intervals:
        if isinstance(item, Interval):
            _validate(item)
            result.append(item)
        else:
            try:
                start, end = item
            except (TypeError, ValueError):
                raise TypeError(
                    "each interval must be an Interval or a (start, end) "
                    "pair; got %r" % (item,)
                )
            iv = Interval(start, end)
            _validate(iv)
            result.append(iv)
    return result


def merge(intervals: Iterable) -> List[Interval]:
    """Merge a set of intervals into the minimal disjoint covering set.

    Adjacent half-open intervals (e.g. [1,3) and [3,5)) are merged into one
    because they tile exactly with no overlap and no gap. Zero-width
    intervals are dropped; they contain no points.
    """
    cleaned = [iv for iv in _normalise(intervals) if iv.start < iv.end]
    if not cleaned:
        return []

    # Sort once; then sweep left to right extending the current interval while
    # the next one starts at or before its end. Because starts are ordered and
    # we only ever grow end, a single linear pass suffices.
    cleaned.sort(key=lambda iv: (iv.start, iv.end))
    out: List[Interval] = []
    cur_start = cleaned[0].start
    cur_end = cleaned[0].end
    for iv in cleaned[1:]:
        if iv.start <= cur_end:
            if iv.end > cur_end:
                cur_end = iv.end
        else:
            out.append(Interval(cur_start, cur_end))
            cur_start = iv.start
            cur_end = iv.end
    out.append(Interval(cur_start, cur_end))
    return out


def _complement_single(iv: Interval, universe: Interval) -> List[Interval]:
    """Compute the complement of one interval against a finite universe.

    Used as a building block for subtraction: A - B can be computed as the
    intersection of A with the complement of B. Working against a finite
    universe keeps results bounded; the caller chooses a universe wide enough
    to cover everything that matters.
    """
    out: List[Interval] = []
    if iv.start > universe.start:
        out.append(Interval(universe.start, iv.start))
    if iv.end < universe.end:
        out.append(Interval(iv.end, universe.end))
    return out


def complement(intervals: Iterable, universe: Interval) -> List[Interval]:
    """Return universe minus the merged intervals.

    The universe is a half-open [start, end). Intervals are merged first so
    overlaps and adjacencies collapse before subtraction.
    """
    _validate(universe)
    merged = merge(intervals)
    # Running cursor over the universe; each merged interval carves a hole.
    result: List[Interval] = []
    cursor = universe.start
    end = universe.end
    for iv in merged:
        if iv.end <= cursor:
            continue
        if iv.start >= end:
            break
        # Clamp into [universe.start, universe.end) so out-of-range inputs do
        # not produce phantom intervals beyond the universe.
        seg_start = max(iv.start, cursor)
        seg_end = min(iv.end, end)
        if seg_start > cursor:
            result.append(Interval(cursor, seg_start))
        cursor = seg_end
        if cursor >= end:
            break
    if cursor < end:
        result.append(Interval(cursor, end))
    return result


def intersect(a: Iterable, b: Iterable) -> List[Interval]:
    """Intersect two sets of intervals.

    Each set is merged first; then a two-pointer sweep finds pairwise overlaps.
    Returns the half-open overlap of the two sets, normalised to sorted,
    disjoint, zero-width-free form.
    """
    ma = merge(a)
    mb = merge(b)
    result: List[Interval] = []
    i = j = 0
    # Classic two-finger merge scan. Because both lists are sorted and
    # disjoint, we never revisit an element and the scan is O(n+m).
    while i < len(ma) and j < len(mb):
        lo = max(ma[i].start, mb[j].start)
        hi = min(ma[i].end, mb[j].end)
        if lo < hi:
            result.append(Interval(lo, hi))
        if ma[i].end < mb[j].end:
            i += 1
        else:
            j += 1
    return result


def subtract(a: Iterable, b: Iterable, universe: Interval) -> List[Interval]:
    """Subtract set b from set a within a fixed universe.

    A finite universe is required because the complement of a half-open
    interval is otherwise unbounded on the side that has no neighbour. This
    is the one design choice a caller must understand: pick a universe that
    spans everything A can cover. The result is intersect(A, complement(B)).
    """
    _validate(universe)
    not_b = complement(b, universe)
    return intersect(a, not_b)
