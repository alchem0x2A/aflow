"""Handle boolean logic in the keywords based on sympy
"""
# from aflow.keywords import Keyword
import sympy
from sympy import Eq, Ne, Ge, Le, Gt, Lt, Implies
from sympy import And, Not, Or, Integer, Float, Symbol
from sympy import simplify_logic
from aflow.keywords import symb_to_keyword

# from aflow.msg import warn
from warnings import warn


def _num_symbols_in_expr(expr, symbol_prefix="x_"):
    """Determine how many expressions are inside the expression"""
    symbols = expr.free_symbols
    valid_symbols = [s for s in symbols if s.name.startswith(symbol_prefix)]
    return len(valid_symbols), valid_symbols


def _expr_priority(expr):
    # Get priority of current expression
    # Larger number get calculated first
    func = expr.func
    if func in (Symbol, Integer, Float):
        return 99  # symbols always come first
    # Unlike normal cases, aflow api allows reading comparison first
    elif func in (Not,):
        return 9
    elif func in (Eq, Ne, Ge, Le, Gt, Lt):
        return 8
    elif func in (And,):
        return 7
    elif func in (Or,):
        return 6
    else:
        raise ValueError(f"{type(func)} is not accepted in current workflow.")


def _join_children(expr, child_strings, keyword=None):
    """Return a valid aflow string combining the operator and child strings
    the symbol_prefix determines what to put before a keyword field
    e.g. Op(x_keyword, value) --> x_keyword(Op(value))
    """
    func = expr.func
    # And / or takes multiple children as inputs
    if func in (And, Or):
        if func == And:
            char = ","
        else:
            char = ":"
        full_string = char.join(child_strings)
        if keyword is not None:
            full_string = f"{keyword}({full_string})"
        return full_string
    elif func in (Not,):
        if len(child_strings) != 1:
            raise ValueError("NOT operator works on only 1 parameter")
        full_string = child_strings[0]
        return f"!{full_string}"
    else:
        # print(expr, expr.func, child_strings)
        if len(child_strings) != 1:
            raise ValueError("children numbers should be less than 2")
        string = child_strings[0]
        if func == Eq:
            full_string = string
        elif func == Ne:
            full_string = "!" + string
        elif func == Ge:
            full_string = string + "*"
        elif func == Le:
            full_string = "*" + string
        elif func == Gt:
            full_string = "!*" + string
        elif func == Lt:
            full_string = "!" + string + "*"
        elif func == Implies:
            # Use wildcard if the operation not known
            # TODO: make sure we're ok
            full_string = "*" + string + "*"
        else:
            full_string = string

        if keyword is not None:
            full_string = f"{keyword}({full_string})"
        return full_string


def _expr_to_strings(expr, symbol_prefix="x_", simplify=False, root=True):
    """Use expression tree to parse the symbols and return a aflow-like api-reference
    If the provided expression has only one known keyword, group all the conditions
    in one bracket.

    Other, use the sequency given by sympy
    parameter `root` controls at which level the keyword should be added
    """
    if not hasattr(expr, "func"):
        raise TypeError(
            f"Expect to take boolean expression but get {type(expr)} instead"
        )
    if root:
        num_symbols, valid_symbols = _num_symbols_in_expr(
            expr, symbol_prefix=symbol_prefix
        )
        # convert keyword
        kw = symb_to_keyword[valid_symbols[0].name]
        if num_symbols > 1:
            # Use fallback mode expression convertion
            # TODO warning
            return _fallback_expr_to_strings(expr, symbol_prefix=symbol_prefix)

    # simplify should only be called at root level and 1 keyword
    # expected simplications are
    if simplify:
        expr = simplify_logic(expr)

    func = expr.func
    args = expr.args
    # Symbol or numerical are always leaf nodes
    # use expr.is_Xxx to determine type instead of func (not working for type One)
    if expr.is_Symbol:
        # Is current expression the keyword?
        if expr.name.startswith(symbol_prefix):
            return None
        else:
            # Wrap expression using single brackets
            return f"'{str(expr)}'"
    elif expr.is_Float:
        return str(float(expr))
    elif expr.is_Integer:
        return str(expr)
    else:
        pass

    # if func in (Symbol, Integer, Float):
    #     if func == Symbol:
    #         # Is current expression the keyword?
    #         if expr.name.startswith(symbol_prefix):
    #             return None
    #         else:
    #             # Wrap expression using single brackets
    #             return f"'{str(expr)}'"
    #     else:
    #         # Reduce the precision of float to default
    #         if func == Float:
    #             return str(float(expr))
    #         else:
    #             return str(expr)

    child_strings = []
    for arg in args:
        # get a partial string from each child
        # Handle only relational nodes
        cstr = _expr_to_strings(arg, symbol_prefix=symbol_prefix, root=False)
        if cstr is None:  # encounters target
            continue
        # determine the priority of operations. wrap lower priority with brackets
        #         if _expr_priority(arg) < _expr_priority(expr):
        #             cstr = "(" + cstr + ")"
        if arg.func in (And, Or):
            cstr = "(" + cstr + ")"
        child_strings.append(cstr)

    # all child calls are fallback mode!
    # import pdb; pdb.set_trace()
    current_string = _join_children(expr, child_strings)
    if root:
        current_string = f"{kw}({current_string})"

    return current_string


def _fallback_join_children(expr, child_strings):
    """'Fallback' mode of joining children string
    Op('keyword', 'val1') --> keyword(Op(val1))
    """
    warn(
        (
            "Mixing multiple filter keyword logic "
            "has only minimal support. Please check the actual outputs of "
            "Query.matchbook() if running into issues.\n"
            "Consider use consecutive calls to Query.filter with only one keyword"
        )
    )
    func = expr.func
    # And / or takes multiple children as inputs
    if func in (And, Or):
        if func == And:
            char = ","
        else:
            char = ":"
        full_string = char.join(child_strings)
        return full_string
    elif func in (Not,):
        if len(child_strings) != 1:
            raise ValueError("NOT operator works on only 1 parameter")
        full_string = child_strings[0]
        return f"!{full_string}"
    else:
        # print(expr, expr.func, child_strings)
        if len(child_strings) != 2:
            raise ValueError("children numbers should be 2")
        # always sort in the way of (keyword, value)
        string = child_strings[0]
        # convert x_keyword --> keyword
        keyword = symb_to_keyword[child_strings[1]]
        if func == Eq:
            full_string = f"{keyword}({string})"
        elif func == Ne:
            full_string = f"{keyword}(!{string})"
        elif func == Ge:
            full_string = f"{keyword}({string}*)"
        elif func == Le:
            full_string = f"{keyword}(*{string})"
        elif func == Gt:
            full_string = f"{keyword}(!*{string})"
        elif func == Lt:
            full_string = f"{keyword}(!{string}*)"
        elif func == Implies:
            # Use wildcard if the operation not known
            # TODO: make sure we're ok
            full_string = f"{keyword}(*{string}*)"
        else:
            full_string = string

        return full_string


def _fallback_expr_to_strings(expr, symbol_prefix="x_"):
    """Use expression tree to parse the symbols and return a aflow-like api-reference
    this is the fall-back mode that works for multiple keywords
    """
    func = expr.func
    args = expr.args
    if expr.is_Symbol:
        # Is current expression the keyword?
        if expr.name.startswith(symbol_prefix):
            return expr.name
        else:
            # Wrap expression using single brackets
            return f"'{str(expr)}'"
    elif expr.is_Float:
        return str(float(expr))
    elif expr.is_Integer:
        return str(expr)
    else:
        pass
    # if func in (Symbol, Integer, Float):
    #     if func == Symbol:
    #         if expr.name.startswith(symbol_prefix):
    #             return expr.name
    #         else:
    #             return f"'{str(expr)}'"
    #     else:
    #         # Reduce the precision of float to default
    #         if func == Float:
    #             return str(float(expr))
    #         else:
    #             return str(expr)

    child_strings = []
    for arg in args:
        cstr = _fallback_expr_to_strings(arg, symbol_prefix)
        if arg.func in (And, Or):
            cstr = "(" + cstr + ")"
        child_strings.append(cstr)

    # Sort the string so that keyword comes last
    child_strings = sorted(child_strings, key=lambda s: s.startswith(symbol_prefix))
    # _fallback_join_children tries to determine the keyword from list of strings
    current_string = _fallback_join_children(expr, child_strings)
    return current_string
