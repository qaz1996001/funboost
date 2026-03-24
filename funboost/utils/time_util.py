# coding=utf-8
import functools
import typing
import datetime
import time
import re
import pytz
from funboost.core.funboost_time import FunboostTime

from funboost.utils import nb_print

@functools.lru_cache()
def _get_funboost_timezone():
    from funboost.funboost_config_deafult import FunboostCommonConfig
    return FunboostCommonConfig.TIMEZONE

def build_defualt_date():
    """
    Get today's and tomorrow's date.
    :return:
    """
    today = datetime.date.today()
    today_str = today.__str__()
    tomorrow = today + datetime.timedelta(days=1)
    tomorrow_str = str(tomorrow)
    return today, tomorrow, today_str, tomorrow_str


def get_day_by_interval(n):
    """
    :param n: Number of days from today, can be positive or negative integer
    :return:
    """
    today = datetime.date.today()
    day = today + datetime.timedelta(days=n)
    day_str = str(day)
    return day, day_str


def get_ahead_one_hour(datetime_str):
    """
    Get the datetime string and timestamp for one hour earlier.
    :return:
    """
    datetime_obj = datetime.datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
    datetime_obj_one_hour_ahead = datetime_obj + datetime.timedelta(hours=-1)
    return datetime_obj_one_hour_ahead.strftime('%Y-%m-%d %H:%M:%S'), datetime_obj_one_hour_ahead.timestamp()


def timestamp_to_datetime_str(timestamp):
    time_local = time.localtime(timestamp)
    # Convert to new time format (2016-05-05 20:28:54)
    return time.strftime("%Y-%m-%d %H:%M:%S", time_local)


class DatetimeConverter:
    """
    The most convenient datetime manipulation approach. Uses real OOP with instantiation; much better calling style than pure static utility classes.
    """
    DATETIME_FORMATTER = "%Y-%m-%d %H:%M:%S"
    DATETIME_FORMATTER2 = "%Y-%m-%d"
    DATETIME_FORMATTER3 = "%H:%M:%S"

    @classmethod
    def bulid_conveter_with_other_formatter(cls, datetime_str, datetime_formatter):
        """
        :param datetime_str: Datetime string
        :param datetime_formatter: Format template that can parse the string
        :return:
        """
        datetime_obj = datetime.datetime.strptime(datetime_str, datetime_formatter)
        return cls(datetime_obj)

    def __init__(self, datetimex: typing.Union[int, float, datetime.datetime, str] = None):  # REMIND Do not set default to datetime.datetime.now() or time.time(), otherwise the default parameter value is evaluated only once
        """
        :param datetimex: Accepts timestamp, datetime object, and datetime string types
        """
        # if isinstance(datetimex, str):
        #     if not re.match(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', datetimex):
        #         raise ValueError('The datetime string format does not match the parameter requirements')
        #     else:
        #         self.datetime_obj = datetime.datetime.strptime(datetimex, self.DATETIME_FORMATTER)
        # elif isinstance(datetimex, (int, float)):
        #     if datetimex < 1:
        #         datetimex += 86400
        #     self.datetime_obj = datetime.datetime.fromtimestamp(datetimex, tz=pytz.timezone(_get_funboost_timezone()))  # Timestamp 0 causes errors on Windows.
        # elif isinstance(datetimex, datetime.datetime):
        #     self.datetime_obj = datetimex
        # elif datetimex is None:
        #     self.datetime_obj = datetime.datetime.now(tz=pytz.timezone(_get_funboost_timezone()))
        # else:
        #     raise ValueError('The parameter passed during instantiation does not meet requirements')
        self.datetime_obj = FunboostTime(datetimex).datetime_obj

    @property
    def datetime_str(self):
        return self.datetime_obj.strftime(self.DATETIME_FORMATTER)

    @property
    def time_str(self):
        return self.datetime_obj.strftime(self.DATETIME_FORMATTER3)

    @property
    def date_str(self):
        return self.datetime_obj.strftime(self.DATETIME_FORMATTER2)

    @property
    def timestamp(self):
        return self.datetime_obj.timestamp()

    @property
    def one_hour_ago_datetime_converter(self):
        """
        Hotels often require free cancellation one hour in advance; encapsulated here for convenience.
        :return:
        """
        one_hour_ago_datetime_obj = self.datetime_obj + datetime.timedelta(hours=-1)
        return self.__class__(one_hour_ago_datetime_obj)

    def is_greater_than_now(self):
        return self.timestamp > time.time()

    def __str__(self):
        return self.datetime_str

    def __call__(self):
        return self.datetime_obj


def seconds_to_hour_minute_second(seconds):
    """
    Convert seconds to hours:minutes:seconds format.
    :param seconds:
    :return:
    """
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return "%02d:%02d:%02d" % (h, m, s)


if __name__ == '__main__':
    """
    1557113661.0
    '2019-05-06 12:34:21'
    '2019/05/06 12:34:21'
    DatetimeConverter(1557113661.0)()
    """
    # noinspection PyShadowingBuiltins
    print = nb_print
    o3 = DatetimeConverter('2019-05-06 12:34:21')
    print(o3)
    print('- - - - -  - - -')

    o = DatetimeConverter.bulid_conveter_with_other_formatter('2019/05/06 12:34:21', '%Y/%m/%d %H:%M:%S')
    print(o)
    print(o.date_str)
    print(o.timestamp)
    print('***************')
    o2 = o.one_hour_ago_datetime_converter
    print(o2)
    print(o2.date_str)
    print(o2.timestamp)
    print(o2.is_greater_than_now())
    print(o2(), type(o2()))
    print(DatetimeConverter())
    print(datetime.datetime.now())
    time.sleep(5)
    print(DatetimeConverter())
    print(datetime.datetime.now())
    print(DatetimeConverter(3600 * 24))

    print(seconds_to_hour_minute_second(3600 * 2))
