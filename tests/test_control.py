"""Tests execution of the search API to retrieve results.
"""
import pytest


def test_len(paper):
    """Tests the code to get the length of a query."""
    assert paper.N > 900


def test_iter(paper):
    """Tests the iterator over individual results in the search
    response. Includes testing the slicing behavior.
    """
    for i, entry in enumerate(paper):
        key = "{} of {}".format(i + 1, paper.N)
        if i < 20:
            assert entry.raw == paper.responses[-1][key]
        else:
            assert entry.raw == paper.responses[-2][key]


def test_Si():
    """Tests a query for silicon prototypes from ICSD."""
    import aflow
    from aflow import K

    Si = (
        aflow.search(catalog="ICSD")
        .filter(K.species == "Si")
        .select(K.positions_cartesian)
        .exclude(K.Egap)
    )

    # We purposefully request across a paging boundary to make sure
    # there is continuity.
    for i, entry in enumerate(Si[90:110]):
        assert "ICSD" in entry.aurl

    # Now, get a single item in a set that we haven't queried yet.
    assert "ICSD" in Si[220].aurl

    # Make sure that the finalization actually works.
    N = len(Si.filters)
    assert Si.filter(K.Egap > 3) is Si
    assert len(Si.filters) == N


def test_ordering():
    """Tests a live query with ordering."""
    from aflow import search, K

    result = (
        search(batch_size=20)
        .select(K.agl_thermal_conductivity_300K)
        .filter(K.Egap > 6)
        .orderby(K.agl_thermal_conductivity_300K, True)
    )
    assert len(result[80].aurl) > 0

    orderby_exclude_result = (
        search(batch_size=20)
        .select(K.agl_thermal_conductivity_300K)
        .filter(K.Egap > 6)
        .orderby(K.auid)
        .exclude(K.auid)
    )

    assert orderby_exclude_result.matchbook().startswith("$auid")


def test_empty_query_result():
    from aflow import search, K

    # Check for auids that end with "aflow", which none do
    result = search(catalog="ICSD", batch_size=20).filter(K.auid < "aflow")
    assert result.N == 0
