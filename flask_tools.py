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
    url_for,
)
from persistent_dict_db import (

    FindOne,
    FindAll,
    Delete,
    Drop,

    PersistentDictDB,
    SetDB_URI,
)
import uuid
import functools

AUTH_TOKEN_EXPIRATION_SECONDS = 60 * 60 * 24 * 365  # seconds

DOMAIN_RE = re.compile('.+\.(.+\.[^\/]+)')


def StripNonHex(string):
    ret = ''
    for c in string.upper():
        if c in '0123456789ABCDEF':
            ret += c
    return ret


def MACFormat(macString):
    # macString can be any string like 'aabbccddeeff'
    macString = StripNonHex(macString)
    return '-'.join([macString[i: i + 2] for i in range(0, len(macString), 2)])


def GetRandomID():
    return HashIt(None)


uniqueID = uuid.getnode()


def HashIt(string=None, salt=uniqueID):
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
    '''
    OTHER KEYS
    
    authToken - unique 512 char string
    lastAuthTokenTime - datatime.datetime that authToken was issued
    '''

    def __setitem__(self, key, value):
        if key == 'email':
            value = value.lower()  # force emails to be lower case

        return super().__setitem__(key, value)

    def __getitem__(self, item):
        if item == 'email':
            item = item.lower()
        return super().__getitem__(item)


def GetApp(appName=None, *a, **k):
    global DB_URI

    import config

    engineURI = k.pop('db_engineURI', 'sqlite:///{}.db'.format(appName.replace(' ', '')))
    SetDB_URI(engineURI)
    devMode = k.pop('devMode', False)

    app = Flask(
        appName,
        *a,
        **k,
    )
    app.config.from_object(config.GetConfigClass(appName)())

    return app


def SetupLoginPage(
        app,
        DB_URI=None,  # None or 'sqlite:///mydatabase.db'
        loginURL='/login',  # used for @app.route
        templatePath=None,  # path like '/login.html'
        templateKey='loginContent',  # used to fill in page with messages
        afterLoginRedirect='/',
):
    if DB_URI is None:
        DB_URI = 'sqlite:///{}.db'.format(app.name)

    if templatePath is None:
        templatePath = 'login.html'
        print('templatePath=', templatePath)

    SetDB_URI(DB_URI)

    @app.route(loginURL, methods=['GET', 'POST'])
    def Login(*a, **k):
        print('Login', a, k)
        email = request.form.get('email', None)
        if email is None:
            email = request.cookies.get('email', None)
        print('email=', email)

        # flash(request.cookies)

        authToken = request.form.get('authToken', None)

        if email is None:
            # The user loaded the page

            # Present them with the login form
            authToken = GetRandomID()

            loginForm = '''
                    <form method="POST" action="{0}">
                        <div class="form-group">
                        Email: <input type="email" name="email">
                        </div><div class="form-group">
                        <input type="hidden" name="authToken" value="{1}">
                        </div><div class="form-group">
                        <input type="submit" value="Send Login Email">
                        </div>
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

                ref = request.referrer
                if ref is None:
                    ref = 'www.grant-miller.com'
                referrerDomainMatch = DOMAIN_RE.search(ref)
                if referrerDomainMatch is not None:
                    referrerDomain = referrerDomainMatch.group(1)
                else:
                    referrerDomain = 'grant-miller.com'

                body = '''
Click here to login now:
http://{0}/auth?email={1}&authToken={2}
                    
                '''.format(
                    referrerDomain,
                    email,
                    authToken,
                )

                # body += '\r\n'
                #
                # for item in dir(request):
                #     print(item, getattr(request, item))
                #     body += '{}={}\r\n'.format(item, getattr(request, item))

                SendEmail(to=email, frm='login@{}'.format(referrerDomain), subject='Login', body=body)
                flash('An email was sent to {}. Please click the link in the email to login.'.format(email))

            return render_template('main.html')

    @app.route('/auth')
    def Auth(*a, **k):
        print('Auth(', a, k)
        email = request.values.get('email', None)
        authToken = request.values.get('authToken', None)
        if authToken is None:
            authToken = request.cookies.get('authToken')
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
            authDT = user.get('lastAuthTokenTime', None)
            if authDT is not None:
                delta = datetime.datetime.now() - authDT
                if delta.total_seconds() < AUTH_TOKEN_EXPIRATION_SECONDS:
                    # good
                    session['email'] = user.get('email')

                    user['authenticated'] = True

                    resp = redirect(afterLoginRedirect)
                    expireDT = datetime.datetime.now() + datetime.timedelta(seconds=AUTH_TOKEN_EXPIRATION_SECONDS)
                    resp.set_cookie(
                        'email', user.get('email'),
                        expires=expireDT,
                        domain=app.config.get('SERVER_NAME', None)
                    )
                    resp.set_cookie(
                        'authToken', authToken,
                        expires=expireDT,
                        domain=app.config.get('SERVER_NAME', None)
                    )
                    return resp

                else:
                    # auth token expired
                    flash('Auth Token expired. Please log in again.')
                    return redirect(url_for(Login))

            else:
                flash('Auth Token has no expiration. This is invalid. Please log in again.')
                return redirect(url_for(Login))

        else:
            return render_template('login_failed.html')


def GetUser(email=None):
    # return user object if logged in, else return None
    # if user provides an email then return that user obj
    print('GetUser(', email)

    if email is None:
        email = session.get('email', None)
    if email is None:
        email = request.cookies.get('email', None)

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


def VerifyLogin(func):
    '''
    Use this decorator on view's that require a log in, it will auto redirect to login page
    :param func:
    :return:
    '''
    print('53 VerifyLogin(', func)

    @functools.wraps(func)
    def VerifyLoginWrapper(*args, **kwargs):
        print('VerifyLoginWrapper(', args, kwargs)
        user = GetUser()
        print('57 user=', user)
        if user is None:
            flash('You must be logged in for that.')
            return redirect('/login')
        else:
            return func(*args, **kwargs)

    return VerifyLoginWrapper
