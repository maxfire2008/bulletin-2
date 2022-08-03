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

