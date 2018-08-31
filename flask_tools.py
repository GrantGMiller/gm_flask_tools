import hashlib
import re
from subprocess import Popen, PIPE
from email.mime.text import MIMEText
import sys
import time
from flask import (
    Flask,
    render_template,
    session,
    request,
    redirect,
    flash,
    make_response,
    Markup,

)
import db_helpers
from forms import (
    LoginForm,
)

def GetRandomID():
    return HashIt(None)


def HashIt(string=None, salt='flask_tools_arbitrary_string'):
    '''
    This function takes in a string and converts it to a unique hash.
    Note: this is a one-way conversion. The value cannot be converted from hash to the original string
    :param string: string, if None a random hash will be returned
    :return: str
    '''
    if string is None:
        # if None a random hash will be returned
        string = str(time.time())

    if not isinstance(string, str):
        string = str(string)

    salt = 'gs_tools_arbitrary_string'
    hash1 = hashlib.sha512(bytes(string, 'utf-8')).hexdigest()
    hash1 += salt
    hash2 = hashlib.sha512(bytes(hash1, 'utf-8')).hexdigest()
    return hash2


def IsValidEmail(email):
    if len(email) > 7:
        if re.match(".+\@.+\..+", email) != None:
            return True
        return False


def SendEmail(to, frm, subject, body):
    if 'linux' in sys.platform:
        msg = MIMEText(body)
        msg["From"] = frm
        msg["To"] = to
        msg["Subject"] = subject
        with Popen(["sendmail", "-t", "-oi"], stdin=PIPE) as p:
            p.communicate(msg.as_string().encode())
            return str(p)


def MoveListItem(l, item, units):
    # units is an pos/neg integer (negative it to the left)
    '''
    Exampe;
    l = ['a', 'b', 'c', 'X', 'd', 'e', 'f','g']
    MoveListItem(l, 'X', -2)
    >>> l= ['a', 'X', 'b', 'c', 'd', 'e', 'f', 'g']

    l = ['a', 'b', 'c', 'X', 'd', 'e', 'f','g']
    MoveListItem(l, 'X', -2)
    >>> l= ['a', 'b', 'c', 'd', 'e', 'X', 'f', 'g']

    '''
    l = l.copy()
    currentIndex = l.index(item)
    l.remove(item)
    l.insert(currentIndex + units, item)
    return l


def ModIndexLoop(num, min_, max_):
    # print('\nMod(num={}, min_={}, max_={})'.format(num, min_, max))

    maxMinDiff = max_ - min_ + 1  # +1 to include min_
    # print('maxMinDiff=', maxMinDiff)

    minToNum = num - min_
    # print('minToNum=', minToNum)

    if minToNum == 0:
        return min_

    mod = minToNum % maxMinDiff
    # print('mod=', mod)

    return min_ + mod


def GetApp(appName=None, *a, **k):
    import config
    app = Flask(
        appName,
        *a,
        **k,
    )
    app.config.from_object(config.GetConfigClass(appName)())
    return app


def SetupLoginPage(
        app,
        loginURL='/login',
        templatePath=None,
        templateKey='loginContent',
        userDatabaseName='Users',
        afterLoginRedirect='/',
):
    @app.route(loginURL, methods=['GET', 'POST'])
    def Login(*a, **k):
        print('Login', a, k)
        email = request.form.get('email', None)
        print('email=', email)

        if email is None:
            # The user loaded the page

            # Present them with the login form
            ID = GetRandomID()

            loginForm = '''
                    <form method="POST" action="{0}">
                        Email: <input type="email" name="email">
                        <input type="hidden" name="ID" value="{1}">
                        <input type="submit" value="Send Login Email">
                    </form>
                '''.format(loginURL, ID)

            return render_template(
                templatePath,
                **{templateKey: Markup(loginForm)},
            )

        else:
            print('Sending email to user to authenticate.')
            if app.debug is True:
                print('app.debug is True, faking the login')
                session['email'] = email
            else:
                # TODO
                print('Sending email to user. ')
                ID = request.form.get('ID')
                SendEmail(to=email, frm='login@{}'.format(appN), subject='Login', body='''
                    Click here to login now:
                    <a href="">Click here to login now:</a>
                ''')
                flash('Test')

            return render_template('main.html')
