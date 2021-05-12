"""Test the fetching for AflowFile works
"""
import pytest
import json
from pathlib import Path
from random import shuffle
from aflow.entries import Entry, AflowFile, AflowFiles
from aflow.msg import warn

curdir = Path(__file__).parent

# Load big json query
with open(curdir / "data_big.json", "r") as fd:
    raw_entries = json.load(fd)
    # convert raw_entries to list and do a random shuffle
    raw_entries = list(raw_entries.values())


def test_query_files(batch=10):
    """test on randomly sampled entries"""
    shuffle(raw_entries)
    for e in raw_entries[:batch]:
        entry = Entry(**e)
        print(entry.aurl)
        # Read the CONTCAR.relax, which should always present
        afile = AflowFile(entry.aurl, "CONTCAR.relax")
        if "CONTCAR.relax" not in entry.files:
            warn(f"{aurl} does not contain CONTCAR.relax file, probably a MD calculation")
            continue
        else:
            assert "CONTCAR.relax" in afile.filename
            # read the content, watch for HTTP404 error
            # hope no http404 error
            content = afile()
            print(content)


def test_aurl_with_colon():
    """Test if aurl with colon can be read."""
    # Series with aurl that contain 0 ~ 3 colons after the edu domain name
    for ncolon in range(4):
        shuffle(raw_entries)
        for e in raw_entries:
            entry = Entry(**e)
            aurl = entry.aurl
            print(entry.aurl)
            # edu:xx --> 2
            if len(aurl.split(":")) == ncolon + 2:
                afile = AflowFile(aurl, "CONTCAR.relax")
                if "CONTCAR.relax" not in entry.files:
                    warn(f"{aurl} does not contain CONTCAR.relax file, probably a MD calculation")
                    continue
                else:
                    assert "CONTCAR.relax" in afile.filename
                    content = afile()
                    print(content)
                    break
