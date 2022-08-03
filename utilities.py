import ast
import statistics
from typing import Union
from types import CodeType
import datetime
import base64
import regex
import bulletin_config


def base64_encode(string):
    if type(string) is str:
        string = string.encode()
    return base64.urlsafe_b64encode(string).decode()


def grades_string(grades: list):
    if -1 in grades:
        return "<i>All Grades</i>"
    else:
        return "<b>"+"</b>, <b>".join(map(str, grades))+"</b>"


def days_to_readable(days: int):
    if days > 0:
        if days == 0:
            return "Today"
        elif days == 1:
            return "Yesterday"
        elif days < 7:
            return f"{days} days ago"
        elif days < 30:
            return f"{days // 7} weeks ago"
        elif days < 365:
            return f"{days // 30} months ago"
        else:
            return f"{days // 365} years ago"
    elif days < 0:
        if days == -1:
            return "Tomorrow"
        elif days > -7:
            return f"{-days} days from now"
        elif days > -30:
            return f"{-days // 7} weeks from now"
        elif days > -365:
            return f"{-days // 30} months from now"
        else:
            return f"{-days // 365} years from now"
    else:
        return "Unknown"


def get_age_from_time(time_from: datetime.datetime):
    # subtract time_from from now
    time_diff = datetime.datetime.now(
    ) - datetime.datetime.combine(time_from, datetime.time())

    days = time_diff.days
    return days


def filter_for_grades(visibilities: list):
    return filter(lambda a: regex.match("grade:[0-9]+", a), visibilities)


class SecurityError(Exception):
    """Indicates a possible security breach
    in parsing boolean statements.
    """


def compile_isolated(
    source: Union[str, ast.Expression], flags: int,
) -> Union[ast.Expression, CodeType]:
    return compile(
        source=source,
        filename='<untrusted_expr>',
        mode='eval',
        flags=flags,
        dont_inherit=1,  # no future features, isolated flags
        optimize=2,      # cut asserts and docstrings
    )


def evaluate(string: str, **locals: bool) -> bool:
    if len(string) > bulletin_config.IF_ELSE_EXPRESSION_LIMIT:
        raise SecurityError('Expression too long')

    expr: ast.Expression = compile_isolated(
        source=string,
        flags=ast.PyCF_ONLY_AST,  # no await, no pep484, defer compilation
    )
    if not isinstance(expr, ast.Expression):
        raise SecurityError('Invalid parent node')

    top_op, = ast.iter_child_nodes(expr)

    for node in ast.walk(top_op):
        print(node)
        if isinstance(node, (
            # ast.UnaryOp,
            ast.Not,
            ast.BoolOp,
            ast.boolop,
            ast.Name,
            ast.Load,
            ast.Compare,
            ast.In,
            ast.NotIn,
            ast.Eq,
            ast.GtE,
            ast.LtE,
            ast.Lt,
            ast.Gt,
        )):
            continue
        if isinstance(node, ast.Constant):
            literal = ast.literal_eval(node)
            if not (isinstance(literal, bool) or isinstance(literal, str) or isinstance(literal, int)):
                raise SecurityError('Invalid literal')
        elif isinstance(node, ast.Call):
            # allow int function
            print(node.func.id)
            if not (isinstance(node.func, ast.Name) and node.func.id == "int"):
                raise SecurityError('Invalid function')
        else:
            raise SecurityError('Invalid node')

    code_object: CodeType = compile_isolated(source=expr, flags=0)

    isolated_globals = {'__builtins__': {}}

    for v in locals.values():
        if not (
            isinstance(v, bool)
            or
            isinstance(v, list)
            or
            isinstance(v, int)
            or
            isinstance(v, dict)
            or
            v in bulletin_config.EXPRESSION_EVALUATION_ALLOWED_FUNCTIONS
        ):
            raise ValueError('Invalid value for locals')

    result = eval(code_object, isolated_globals, locals)
    if not isinstance(result, bool):
        raise SecurityError('Unexpected non-boolean output')

    return result
