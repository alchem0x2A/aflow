"""Test if reading atoms object can work, especially for POSCAR format vasp4.xx"""
"""Test the fetching for AflowFile works
"""
import pytest
import json
from pathlib import Path
from random import shuffle
from aflow.entries import Entry

curdir = Path(__file__).parent

# Load big json query
with open(curdir / "data_big.json", "r") as fd:
    raw_entries = json.load(fd)
    # convert raw_entries to list and do a random shuffle
    raw_entries = list(raw_entries.values())


def test_atoms_read(batch=50):
    """test on randomly sampled entries"""
    shuffle(raw_entries)
    for e in raw_entries[:batch]:
        print(e["aurl"])
        entry = Entry(**e)
        # Read the CONTCAR.relax, which should always present
        atoms = entry.atoms()
        assert atoms is not None


def test_noatom_entries():
    """Corner cases for some entries in LIB5 and LIB6 (AIMD runs)"""
    pass


# def test_aurl_with_colon():
#     """Test if aurl with colon can be read."""
#     # Series with aurl that contain 0 ~ 3 colons after the edu domain name
#     for ncolon in range(4):
#         shuffle(raw_entries)
#         for entry in raw_entries:
#             aurl = entry["aurl"]
#             # edu:xx --> 2
#             if len(aurl.split(":")) == ncolon + 2:
#                 afile = AflowFile(aurl, "CONTCAR.relax")
#                 assert "CONTCAR.relax" in afile.filename
#                 content = afile()
#                 print(aurl, content)
#                 break
