'''
A test site to verify functionality
'''
import datetime
import random

from flask import (
    render_template,
    request,
    redirect,
)
from flask_tools import (
    GetApp,
    GetMenu,
    AddMenuOption,
    GetJobs,
    ScheduleJob,
    ScheduleIntervalJob,
    RemoveJob,
    AddJob,
    SetAdmin,
    SetupRegisterAndLoginPageWithPassword,
    VerifyLogin,
)
import time

app = GetApp('Test Site')

SetAdmin('grant@grant-miller.com')

SetupRegisterAndLoginPageWithPassword(
    app,
    mainTemplate='main.html',
    redirectSuccess='/'
)

AddMenuOption('Schedule Job', '/schedule/job')


@app.route('/')
@VerifyLogin
def Index():
    return render_template(
        'main.html',
        menuOptions=GetMenu()
    )


def ScheduleCallback(*args, **kwargs):
    print(datetime.datetime.utcnow(), ': ScheduleCallback(args=', args, ', kwargs=', kwargs)
    time.sleep(1)
    # if random.randint(0, 10) == 0:
    #     raise Exception('oops')


@app.route('/schedule/job', methods=['GET', 'POST'])
def Schedule_Job():
    if request.form:
        print('request.form=', request.form)
        if request.form.get('delay'):
            if request.form.get('delay') == '0':
                AddJob(
                    func=ScheduleCallback,
                    args=('ASAP',),
                    kwargs={
                        'kw1': 'kw1',
                        'kw2': 'kw2',
                        't': time.asctime(),
                    }
                )
            else:
                ScheduleJob(
                    dt=datetime.datetime.utcnow() + datetime.timedelta(seconds=int(request.form.get('delay'))),
                    func=ScheduleCallback,
                    args=('Schedule delay =', int(request.form.get('delay'))),
                    kwargs={
                        'kw1': 'kw1',
                        'kw2': 'kw2',
                        't': time.asctime(),
                    }
                )
        elif request.form.get('interval'):
            ScheduleIntervalJob(
                func=ScheduleCallback,
                args=('Repeat interval=', int(request.form.get('interval'))),
                seconds=int(request.form.get('interval')),
                kwargs={
                    'kw1': 'kw1',
                    'kw2': 'kw2',
                    't': time.asctime(),
                }
            )

    return render_template(
        'scheduleJob.html',
        jobs=GetJobs(),
    )


# for i in range(3):
#     AddJob(
#         func=ScheduleCallback,
#         args=('addjob',),
#         kwargs={'kw1': '{i} kw add job' + time.asctime()}
#     )
# for i in range(3):
#     ScheduleJob(
#         dt=datetime.datetime.utcnow() + datetime.timedelta(seconds=i),
#         func=ScheduleCallback,
#         args=(f'i={i}',)
#     )


@app.route('/remove/job/<jobID>')
def FlaskRemoveJob(jobID):
    RemoveJob(jobID)
    return redirect('/schedule/job')


if __name__ == '__main__':
    app.run(
        debug=True,
        threaded=True,
    )
