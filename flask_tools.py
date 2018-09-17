import hashlib
import re
from subprocess import Popen, PIPE
from email.mime.text import MIMEText
import sys
import time
import datetime
from flask import (
    Flask,
    render_template,
    session,
    request,
    redirect,
    flash,
    Markup,

)
from persistent_dict_db import (

    FindOne,
    FindAll,
    Delete,
    Drop,

    PersistentDictDB,
    SetDB_URI,
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


class UserClass(PersistentDictDB):
    uniqueKeys = ['email']

    def __setitem__(self, key, value):
        if key == 'email':
            value = value.lower() # force emails to be lower case

        return super().__setitem__(key, value)

    def __getitem__(self, item):
        if item == 'email':
            item = item.lower()
        return super().__getitem__(item)


def GetApp(appName=None, *a, **k):
    global DB_URI

    import config

    engineURI = k.pop('db_engineURI', 'sqlite:///test.db')
    devMode = k.pop('devMode', False)

    app = Flask(
        appName,
        *a,
        **k,
    )
    app.config.from_object(config.GetConfigClass(appName)())

    DB_URI = engineURI

    return app


def SetupLoginPage(
        app,
        DB_URI,
        loginURL='/login',
        templatePath=None,
        templateKey='loginContent',
        afterLoginRedirect='/',
):
    SetDB_URI(DB_URI)

    @app.route(loginURL, methods=['GET', 'POST'])
    def Login(*a, **k):
        print('Login', a, k)
        email = request.form.get('email', None)
        print('email=', email)

        authToken = request.form.get('authToken', None)

        if email is None:
            # The user loaded the page

            # Present them with the login form
            authToken = GetRandomID()

            loginForm = '''
                    <form method="POST" action="{0}">
                        Email: <input type="email" name="email">
                        <input type="hidden" name="authToken" value="{1}">
                        <input type="submit" value="Send Login Email">
                    </form>
                '''.format(loginURL, authToken)

            return render_template(
                templatePath,
                **{templateKey: Markup(loginForm)},
            )

        else:
            # The user submitted the form.
            # Send an email to the address they entered with the authToken
            # If they click the link in the email
            # Check that the auth token and email match

            print('Sending email to user to authenticate.')

            # for item in dir(request):
            #     print(item, getattr(request, item))

            authToken = request.form.get('authToken')

            existingUser = FindOne(UserClass, email=email)

            print('199 existingUser=', existingUser)

            if existingUser is not None:
                existingUser['authToken'] = authToken
                existingUser['lastAuthTokenTime'] = datetime.datetime.now()

            else:
                # no user exist, create a new one
                newUser = UserClass(
                    email=email,
                    authToken=authToken,
                    lastAuthTokenTime=datetime.datetime.now(),
                )
                print('221 newUser=', newUser)

            if app.debug is True:
                print('app.debug is True, faking the login')
                print('redirecting to auth page')
                return redirect('/auth?email={}&authToken={}'.format(email, authToken))
            else:
                # TODO
                print('Sending email to user. ')

                body = '''
                    <a href="http://{0}/auth?email={1}&authToken={2}">
                    Click here to login now:
                    </a>
                '''.format(
                    request.url_root,
                    email,
                    authToken,
                )

                SendEmail(to=email, frm='login@{}'.format(request.url_root), subject='Login', body=body)
                flash('Test')

            return render_template('main.html')

    @app.route('/auth')
    def Auth(*a, **k):
        print('Auth(', a, k)
        email = request.values.get('email', None)
        authToken = request.values.get('authToken', None)
        print('email=', email)
        print('auth=', authToken)

        print('227 FindAll=', list(FindAll(UserClass)))

        user = FindOne(
            UserClass,
            email=email,
            authToken=authToken,
        )

        print('246 user=', user)

        if user is not None:
            session['email'] = user.get('email')

            user['authenticated'] = True

            return redirect(afterLoginRedirect)

        else:
            return render_template('login_failed.html')


def GetUser(email=None):
    # return user object if logged in, else return None
    # if user provides an email then return that user obj
    print('GetUser(', email)

    if email is None:
        email = session.get('email', None)

    print('258 session email=', email)
    try:
        userObj = FindOne(UserClass, email=email)
        print('274 userObj=', userObj)

        if userObj is not None:
            if userObj.get('authenticated') is True:
                return userObj
            else:
                return None

    except Exception as e:
        print(236, e)
        return None


def LogoutUser():
    print('LogoutUser()')
    user = GetUser()
    print('288 user=', user)
    if user is not None:
        user['authenticated'] = False
