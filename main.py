'''
A test site to verify functionality
'''
import datetime

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
    SetAdmin,
)
import time

app = GetApp('Test Site')

AddMenuOption('Schedule Job', '/schedule/job')


@app.route('/')
def Index():
    return render_template(
        'main.html',
        menuOptions=GetMenu()
    )


def ScheduleCallback(*args, **kwargs):
    print(time.asctime(), ': ScheduleCallback(args=', args, ', kwargs=', kwargs)


@app.route('/schedule/job', methods=['GET', 'POST'])
def Schedule_Job():
    if request.form:
        print('request.form=', request.form)
        if request.form.get('delay'):
            ScheduleJob(
                datetime.datetime.now() + datetime.timedelta(seconds=int(request.form.get('delay'))),
                ScheduleCallback,
                1, 2, 3,
                kw1='kw1',
                kw2='kw2',
                t=time.asctime(),
            )
        elif request.form.get('interval'):
            ScheduleIntervalJob(
                ScheduleCallback,
                1, 2, 3,
                seconds=int(request.form.get('interval')),
                kw1='kw1',
                kw2='kw2',
                t=time.asctime(),
            )

    return render_template(
        'scheduleJob.html',
        jobs=GetJobs(),
    )


@app.route('/remove/job/<jobID>')
def FlaskRemoveJob(jobID):
    RemoveJob(jobID)
    return redirect('/schedule/job')


if __name__ == '__main__':
    app.run(debug=True)
