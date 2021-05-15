"""
New tests on the json-schema
Tests the behavior of the keywords with each of the different
operators supported by the AFLUX standard.
"""
# from aflow.keywords_json import K
from aflow import K
from aflow.logic import _expr_to_strings, _num_symbols_in_expr
import pytest


def test_num_variables():
    cond1 = (K.Egap > 6) & (K.species == "Ba")
    cond2 = ((K.Egap > 6) & (K.Egap < 9)) | ((K.Egap > 2) & (K.Egap < 5))
    assert _num_symbols_in_expr(cond1)[0] == 2
    assert _num_symbols_in_expr(cond2)[0] == 1


# def test_load():
#     """Tests keyword loading into dict"""
#     from aflow.keywords import load

#     kws_from_module = K.__dict__
#     loaded_kws = dict()
#     load(loaded_kws)

#     for kw, obj in loaded_kws.items():
#         assert kw in kws_from_module
#         assert obj is kws_from_module[kw]

def test_type():
    # in some cased 1 is treated as sympy.One
    assert _expr_to_strings(K.Egap > 1)
    # float version
    assert _expr_to_strings(K.Egap > 1.0)
    # multiple variables
    assert _expr_to_strings((K.Egap > 1.0) & (K.Egap < 2.0))

    # Following expression will raise TypeError
    with pytest.raises(TypeError):
        _expr_to_strings(K.Egap)

    with pytest.raises(TypeError):
        _expr_to_strings("Egap(1*)")



def test_operators():
    """Test operators. All tests in this function are 1 variable"""

    # and
    k0 = (K.nspecies >= 2) & (K.nspecies <= 4)
    assert _expr_to_strings(k0) == "nspecies(2*,*4)"

    k1 = (K.Egap >= 6) & (K.PV_cell <= 13)
    assert _expr_to_strings(k1) == "Egap(6*),PV_cell(*13)"

    k2 = (K.Egap == 6) & (K.PV_cell == 13)
    assert _expr_to_strings(k2) == "Egap(6),PV_cell(13)"

    k3 = (K.Egap == 6) & (K.PV_cell != 13)
    assert _expr_to_strings(k3) == "Egap(6),PV_cell(!13)"

    k4 = (K.data_source == "aflowlib") | (K.species % "Si")
    assert _expr_to_strings(k4) == "data_source('aflowlib'):species(*'Si'*)"

    k5 = (K.data_source > "aflow") & (K.species < "Ag")
    assert _expr_to_strings(k5) == "data_source(!*'aflow'),species(!'Ag'*)"



def test_invert():
    from sympy import simplify_logic

    k0 = (K.Egap > 6) & (K.PV_cell < 13)
    kn0 = ~k0
    # The not simplifies version
    assert _expr_to_strings(kn0) == "!(Egap(!*6),PV_cell(!13*))"
    
    kn0 = simplify_logic(kn0)
    strings =  _expr_to_strings(kn0)
    assert ":" in strings
    for itm in strings.split(":"):
        assert "!" not in itm


#     reset()

    k1 = (K.Egap >= 6) & (K.PV_cell <= 13)
    kn1 = simplify_logic(~k1)
    strings =  _expr_to_strings(kn1)
    assert ":" in strings
    for itm in strings.split(":"):
        assert "!" in itm

def test_self():
    """Tests combinations of multiple conditions against the same
    keyword.
    """
    k0 = ((K.Egap > 6) | (K.Egap < 21)) & (K.PV_cell < 13)
    # multiple keywords by default do not combine
    assert sorted(_expr_to_strings(k0).split(",")) == ["(Egap(!*6):Egap(!21*))",
                                                       "PV_cell(!13*)"]

#     reset()
#     k1 = ((K.Egap > 6) | (K.Egap < 21)) & ((K.PV_cell < 13) | (K.PV_cell > 2))
#     assert str(k1) == "Egap(!*6:!21*),PV_cell(!13*:!*2)"
#     assert str(K.Egap) == "Egap(!*6:!21*)"
#     assert str(K.PV_cell) == "PV_cell(!13*:!*2)"

#     reset()
    k2 = ((K.Egap > 0) & (K.Egap < 2)) | ((K.Egap > 5) | (K.Egap < 7))
    # Bracket for the other OR is omitted
    assert _expr_to_strings(k2) == "Egap(!*5:!7*:(!*0,!2*))"

#     reset()
    k3 = ((K.Egap > 0) & (K.Egap < 2)) | (K.Egap == 5)
    assert _expr_to_strings(k3) == "Egap(5:(!*0,!2*))"
#     assert str(k2) == 

#     reset()
#     k4 = ((K.Egap >= 6) | (K.Egap <= 21)) & (K.PV_cell <= 13)
#     assert str(k4) == "Egap(6*:*21),PV_cell(*13)"

#     reset()
#     k5 = ((K.Egap >= 6) | (K.Egap <= 21)) & ((K.PV_cell <= 13) | (K.PV_cell >= 2))
#     assert str(k5) == "Egap(6*:*21),PV_cell(*13:2*)"
#     assert str(K.Egap) == "Egap(6*:*21)"
#     assert str(K.PV_cell) == "PV_cell(*13:2*)"

#     reset()
    k6 = ((K.Egap >= 0) & (K.Egap <= 2)) | ((K.Egap >= 5) & (K.Egap <= 7))
    assert _expr_to_strings(k6) == "Egap((0*,*2):(5*,*7))"

#     reset()
    k7 = ((K.Egap >= 0) & (K.Egap <= 2)) | (K.Egap != 5)
    assert _expr_to_strings(k7) == "Egap(!5:(0*,*2))"


# def test_corner():
#     """Tests corner cases that aren't part of the previous tests."""
#     from aflow.keywords import reset

#     assert str(K.geometry) == "geometry"
#     reset()
#     k = K.Egap > 0
#     with pytest.raises(ValueError):
#         k3 = (K.Egap < 2) | (K.Egap == 5)
