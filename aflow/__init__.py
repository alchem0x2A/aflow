from aflow.control import search
from aflow.keywords import K

# _keywords = []
# """list of `str` keyword names available in AFLOW.
# """


def list_keywords():
    """Returns a list of all possible keywords available in the current version of
    AFLOW lib.
    """
    from aflow.keywords import all_keywords

    return list(all_keywords.keys())


# import aflow.keywords as K
