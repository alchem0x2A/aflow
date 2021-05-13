"""All keywords from the AAPI-schema that comes with AFLOW engine
"""
import aflow
from aflow.msg import warn
import json
from pathlib import Path
import requests
import types
from copy import deepcopy
from aflow.msg import warn

from sympy import Symbol, Float, Integer
from sympy import Eq, Ne, Ge, Le, Gt, Lt
from sympy import And, Not, Or


from types import SimpleNamespace

api_folder = Path(aflow.__file__).parent / "api"
schema_file = api_folder / "aapi-schema.json"


def _param_to_symbol(param):
    """Convert the parameter to sympy symbol if possible"""
    if isinstance(param, float):
        return Float(param)
    elif isinstance(param, int):
        return Integer(param)
    else:
        # Just convert the string to a variable, whatever
        return Symbol(str(param))


class Keyword(object):
    """Represents an abstract keyword that can be sub-classed for a
    specific material attribute. This class also represents logical
    operators that define search queries. The combination of two
    keywords with a logical operator produces one more keyword, but
    which has its :attr:`state` altered.

    Args:
        state (str): current query state of this keyword (combination).

    Attributes:
        state (list): of `str` *composite* queries for this keyword (combination).
        ptype (type): python type that values for this keyword will have.
        name (str): keyword name to use in the AFLUX request.
        cache (list): of `str` *simple* operator comparisons.
        classes (set): of `str` keyword names that have been combined into the
          current keyword.
    """

    name = ""
    ptype = None
    atype = None

    def __init__(self):
        """initialize the symbols"""
        self.symbol = Symbol("x_" + self.name.lower())

    def __hash__(self):
        return hash(self.name)

    def __str__(self):
        return name

    def __le__(self, other):
        """Use sympy to compare"""
        return Le(self.symbol, _param_to_symbol(other))

    def __ge__(self, other):
        return Ge(self.symbol, _param_to_symbol(other))

    def __lt__(self, other):
        return Lt(self.symbol, _param_to_symbol(other))

    def __gt__(self, other):
        return Gt(self.symbol, _param_to_symbol(other))

    # def __mod__(self, other):
    #     assert isinstance(other, string_types)
    #     self.cache.append("*'{0}'*".format(other))
    #     return self

    def __eq__(self, other):
        return Eq(self.symbol, _param_to_symbol(other))

    def __ne__(self, other):
        return Ne(self.symbol, _param_to_symbol(other))

    def __and__(self, other):
        raise NotImplementedError("Should not use AND directly with keyword")

    def __or__(self, other):
        raise NotImplementedError("Should not use OR directly with keyword")

    def __invert__(self):
        raise NotImplementedError("Should not use NOT directly with keyword")


def download_schema():
    url = "http://aflow.org/API/aapi-schema"
    warn("AAPI-SCHEMA file not found. Download from {:s}".format(url))
    req = requests.get(url)
    req.encoding = "utf-8"
    # No error check for the moment
    json_dict = json.loads(req.text)
    return json_dict


# Parse the current schema file from aflow
# if it does not exist for some reason
# download from AFLOWLIB
if schema_file.is_file():
    try:
        with open(schema_file, "r") as fd:
            aapi_schema = json.load(fd)
    except Exception:
        aapi_schema = download_schema()
else:
    aapi_schema = download_schema()


def _construct_docstring(dic):
    """Construct a simple doc string from fields in the dictionary"""
    dic = deepcopy(dic)  # avoid deletion in the original dictionary
    exclude_fields = ["__comment__", "status", "verification"]
    docstring = []
    docstring.append(dic.pop("title", "").capitalize())
    docstring.append(dic.pop("description", ""))
    docstring.append("")
    for key, value in dic.items():
        if key not in exclude_fields:
            docstring.append(f"{key}:\t{value}")

    return "\n".join(docstring)


def _determine_type(dic):
    """Determin the `atype`, `ptype` and `delimiter` of the keyword
    now expand `ptype`:
    can be either `float`, `int`
    or a combination of (list, `float`)
    """
    known_types = ("number", "numbers", "string", "strings")
    atype = dic.get("type", "string")
    format = dic.get("format", "%s")

    if atype not in known_types:
        raise ValueError(
            (
                f"AFLOW type {atype} is not valid, "
                "is the AAPI-schema correctly loaded?"
            )
        )

    # determine whether atype needs to be a list
    if atype == "number":
        if format == "%d":
            ptype = int
        elif format == "%g":
            ptype = float
        else:
            ptype = float
            warn(
                (
                    f"{format} incompatible with {atype} in {dic['title']}"
                    "This is a bug in tha AAPI-schema, I'm assuming the numbers are float"
                )
            )
    elif atype == "numbers":
        if format == "%d":
            ptype = (list, int)
        elif format == "%g":
            ptype = (list, float)
        else:
            ptype = (list, float)
            warn(
                (
                    f"{format} incompatible with {atype} in {dic['title']}"
                    "This is a bug in tha AAPI-schema, I'm assuming the numbers are float"
                )
            )
    elif atype == "string":
        ptype = str
    else:  # atype == "strings"
        ptype = (list, str)

    # get the delimiters
    if atype in ("numbers", "strings"):
        # Default delimiter is dot
        delimiter = dic.get("delimiter", ";,")
        # some keywords have strange delimiter type, use ";," as default
        if delimiter not in (",", ":,"):
            delimiter = ";,"
    else:
        delimiter = None

    return atype, ptype, delimiter


def dynamic_class_creation(name, base=object):
    """Dynamically create keyword classes using the
    JSON schema provided by AFLOW
    """
    # Protected name in the schema
    if name in [
        "__schema^2__",
    ]:
        return None
    schema_entry = aapi_schema["AAPI_schema"][name]
    helper_string = _construct_docstring(schema_entry)
    atype, ptype, delimiter = _determine_type(schema_entry)
    status = schema_entry.get("status", "production")

    new_class = type(
        name,
        (base,),
        dict(
            __doc__=helper_string,
            name=name,
            atype=atype,
            ptype=ptype,
            delimiter=delimiter,
            status=status,
        ),
    )
    return new_class


all_keywords = []
k_dict = {}
symb_to_keyword = {}  # mapping from variable to class name

# Dynamically create keywords classes based on the name
for name in aapi_schema["AAPI_schema"].keys():
    new_class = dynamic_class_creation(name, base=Keyword)
    if new_class:
        all_keywords.append(name)
    if new_class is not None:
        # Put the new class under current namespace
        vars()[name] = new_class
        # Make an instance
        inst_ = new_class()
        k_dict[name] = inst_
        # put the
        symb_to_keyword[inst_.symbol.name] = inst_.name

# Now the tricky part, replace the original K with our K
# this should give equivalent K.keyword == xxx etc
K = SimpleNamespace(**k_dict)
