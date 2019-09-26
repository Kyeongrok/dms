import datetime

from dateutil.parser import parse


def str_to_datetime(string):
    if isinstance(string, datetime.datetime):
        return string
    return parse(string)


def datetime_to_str(dt):
    return dt.strftime("%Y%m%dT%H%M%S")


def build_scenario_id(name, user):
    return '-'.join((name, user))
