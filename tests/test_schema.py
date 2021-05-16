""" Test functions downloading AAPI schema
"""
import pytest
from aflow.keywords import download_schema, schema_file, all_keywords


def test_download():
    schema_dict = download_schema()
    for key in ["AAPI_valid", "AAPI_schema"]:
        assert key in schema_dict.keys()
    assert "__schema^2__" in schema_dict["AAPI_schema"].keys()

    for key in all_keywords:
        assert key in schema_dict["AAPI_schema"].keys()
