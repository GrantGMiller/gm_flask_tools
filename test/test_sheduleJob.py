import time

from flask_tools import ScheduleJob
import datetime


def Callback(*args, **kwargs):
    print('Callback(', args, kwargs)


for i in range(-5, 10):
    ScheduleJob(
        datetime.datetime.now() + datetime.timedelta(seconds=i),
        Callback,
        f'i={i}', 'arg0', 'arg1',
        kwarg1='kwarg1',
        kwarg2='kwarg2',
    )

for i in range(6, 8):
    ScheduleJob(
        datetime.datetime.now() + datetime.timedelta(seconds=i),
        Callback,
        f'i={i} doublebook', 'arg0', 'arg1',
        kwarg1='kwarg1',
        kwarg2='kwarg2',
    )

