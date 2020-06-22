from flask_tools import AddJob, ScheduleJob, IsJobComplete
import time
import os
import datetime


def test_Job():
    try:
        os.remove('ft.log')
    except:
        pass

    y = 1

    def Callback(x):
        nonlocal y
        ret = y = x * 2
        return ret

    jobID = AddJob(Callback, y)

    while not IsJobComplete(jobID):
        time.sleep(0.1)

    assert y == 2


def test_JobFail():
    AddJob(lambda x: float(x), 'not a boat')


def test_Schedule():
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
