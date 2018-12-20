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
from collections import namedtuple
import os
from pathlib import Path

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


def IsValidIPv4(ip):
    '''
    Returns True if ip is a valid IPv4 IP like '192.168.254.254'
    Example '192.168.254.254' > return True
    Example '192.168.254.300' > return False
    :param ip: str like '192.168.254.254'
    :return: bool
    '''
    # print('96 IsValidIPv4(', ip)
    if not isinstance(ip, str):
        return False
    else:
        ip_split = ip.split('.')
        if len(ip_split) != 4:
            return False

        for octet in ip_split:
            try:
                octet_int = int(octet)
                if not 0 <= octet_int <= 255:
                    return False
            except:
                return False

        return True


def SendEmail(to, frm=None, subject=None, body=None):
    if frm is None:
        ref = request.referrer
        if ref is None:
            ref = 'www.grant-miller.com'
        referrerDomainMatch = DOMAIN_RE.search(ref)
        if referrerDomainMatch is not None:
            referrerDomain = referrerDomainMatch.group(1)
        else:
            referrerDomain = 'grant-miller.com'

        frm = 'admin@' + referrerDomain

    if subject is None:
        subject = 'Info'

    if body is None:
        body = '<empty body. sorry :-('

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

    displayableAppName = appName

    dbName = appName.replace(' ', '')
    appName = dbName.replace('.', '_')
    dbName = dbName.replace('.', '_')
    engineURI = k.pop('db_engineURI', 'sqlite:///{}.db'.format(dbName))

    SetDB_URI(engineURI)
    devMode = k.pop('devMode', False)

    app = Flask(
        appName,
        *a,
        **k,
    )
    app.config.from_object(config.GetConfigClass(appName)())

    app.jinja_env.globals['displayableAppName'] = displayableAppName

    return app


def SetupLoginPage(
        app,
        DB_URI=None,  # None or 'sqlite:///mydatabase.db'
        loginURL='/login',  # used for @app.route
        templatePath=None,  # path like '/login.html'
        templateKey='loginContent',  # used to fill in page with messages
        afterLoginRedirect='/',
):
    '''
    This sets up the login page with no password
    :param app:
    :param DB_URI:
    :param loginURL:
    :param templatePath:
    :param templateKey:
    :param afterLoginRedirect:
    :return:
    '''
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
            # The user submitted the form, or cookie email found
            # Send an email to the address they entered with the authToken
            # If they click the link in the email
            # Check that the auth token and email match

            authToken = request.form.get('authToken')
            print('authToken=', authToken, type(authToken))

            # for item in dir(request):
            #     print(item, getattr(request, item))

            existingUser = FindOne(UserClass, email=email)

            print('199 existingUser=', existingUser, type(existingUser))

            if authToken is not None:
                if existingUser is not None:
                    existingUser['authToken'] = authToken
                    existingUser['lastAuthTokenTime'] = datetime.datetime.now()

                else:
                    print('no user exist, create a new one')
                    newUser = UserClass(
                        email=email,
                        authToken=authToken,
                        lastAuthTokenTime=datetime.datetime.now(),
                    )
                    print('221 newUser=', newUser)

                print('Sending email to user to authenticate.')

                if app.debug is True:
                    print('app.debug is True, faking the login')
                    print('redirecting to auth page')
                    return redirect('/auth?email={}&authToken={}'.format(email, authToken))

                else:
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
            else:
                print('no auth token, show login page')

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
                    'login.html',
                    **{templateKey: Markup(loginForm)},
                )

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
            flash('Error 348. Login Failed')
            return render_template('login_failed.html')


def GetUser(email=None):
    # return user object if logged in, else return None
    # if user provides an email then return that user obj
    print('GetUser(', email)

    if email is None:
        email = session.get('email', None)
    if email is None:  # check again
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
        session['email'] = None


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


MenuOptionClass = namedtuple('MenuOptionClass', ['title', 'url'])


def SetupRegisterAndLoginPageWithPassword(
        app,
        redirectSuccess=None,
        callbackFailedLogin=None,
        callbackNewUserRegistered=None,
        loginTemplate=None,
        registerTemplate=None,
        forgotTemplate=None,
):
    '''
    Use this function with the @VerifyLogin decorator to simplify login auth

    form should have at least two elements

    '''

    if 'win' in sys.platform:
        mainPath = Path(os.path.dirname(sys.modules['__main__'].__file__))
        TEMPLATES_PATH = mainPath / 'templates'
    else:
        TEMPLATES_PATH = Path('/home/flask_signage/templates')

    if loginTemplate is None:
        templateName = 'autogen_login.html'
        loginTemplate = templateName

        with open(str(TEMPLATES_PATH / templateName), mode='wt') as file:
            file.write('''
                {% extends "main.html" %}
                {% block content %}
                <div class="container">
                
                    <form class="form-signin" method="post">
                        <h2 class="form-signin-heading">Please sign in</h2>
                        
                        <label for="inputEmail" class="sr-only">Email address</label>
                        <input name="email" type="email" id="inputEmail" class="form-control" placeholder="Email address" required autofocus>
                        
                        <label for="inputPassword" class="sr-only">Password</label>
                        <input name="password" type="password" id="inputPassword" class="form-control" placeholder="Password" required>
                        
                        <div class="checkbox">
                            <label>
                                <input name="rememberMe" type="checkbox"> Remember me
                            </label>
                        </div>
                        <button class="btn btn-lg btn-primary btn-block" type="submit">Sign in</button>
                
                        {{messages}}
                
                    </form>
                <br><br>
                <a href="/register">New here? Create an account.</a><br><br>
                <a href="/forgot">Forgot Password</a>
                </div> <!-- /container -->
                {% endblock %}
        ''')

    if registerTemplate is None:
        templateName = 'autogen_register.html'
        registerTemplate = templateName
        with open(str(TEMPLATES_PATH / templateName), mode='wt') as file:
            file.write('''
            {% extends "main.html" %}
            {% block content %}
            <div class="container">
            
                <form class="form-signin" method="post">
                    <h2 class="form-signin-heading">Create a new account:</h2>
                    
                    <label for="inputEmail" class="sr-only">Email address</label>
                    <input name="email" type="email" id="inputEmail" class="form-control" placeholder="Email address" required autofocus>
                    
                    <label for="inputPassword" class="sr-only">Password</label>
                    <input name="password" type="password" id="inputPassword" class="form-control" placeholder="Password" required>
                    
                    <label for="inputPassword" class="sr-only">Password</label>
                    <input name="passwordConfirm" type="password" id="inputPassword" class="form-control" placeholder="Password" required>
                    
                    <div class="checkbox">
                        <label>
                            <input value="rememberMe" type="checkbox" {% if rememberMe %} checked {% endif %}> Remember me
                        </label>
                    </div>
                    <button class="btn btn-lg btn-primary btn-block" type="submit">Sign in</button>
            
                    {{messages}}
            
                </form>
            
                <a href="/">Cancel</a><br>
                <a href="/login">Sign In</a>
            </div> <!-- /container -->
            {% endblock %}
        ''')

    LOGIN_FAILED_FLASH_MESSAGE = 'Username and/or Password is incorrect. Please try again.'

    @app.route('/login', methods=['GET', 'POST'])
    def Login():
        email = request.form.get('email', None)
        password = request.form.get('password', None)
        rememberMe = request.form.get('rememberMe', False)
        if rememberMe is not False:
            rememberMe = True

        print('email=', email)
        # print('password=', '*' * len(password))
        print('rememberMe=', rememberMe)

        if request.method == 'POST':
            # flash messages if needed
            if password is None:
                flash('Please enter a password.')

            if email is None:
                flash('Please enter a username.')

            if email is not None and password is not None:
                passwordHash = HashIt(password)
                userObj = FindOne(UserClass, email=email)
                print('572 userObj=', userObj)
                if userObj is None:
                    # username not found
                    flash(LOGIN_FAILED_FLASH_MESSAGE, 'error')
                    if callable(callbackFailedLogin):
                        callbackFailedLogin()

                    return render_template(
                        loginTemplate,
                        rememberMe=rememberMe,
                    )
                else:
                    if userObj.passwordHash == passwordHash:
                        userObj.authenticated = True
                        session['email'] = email
                        if redirectSuccess:
                            return redirect(redirectSuccess)

                        else:
                            return redirect('/')

                    else:
                        # password mismatch
                        flash(LOGIN_FAILED_FLASH_MESSAGE, 'error')
                        if callable(callbackFailedLogin):
                            callbackFailedLogin()

                        else:
                            return redirect('/login')

            else:
                # user did not enter a email/password, try again
                return render_template(
                    loginTemplate,
                    rememberMe=rememberMe,
                )

        return render_template(
            loginTemplate,
            rememberMe=rememberMe,
        )

    @app.route('/register', methods=['GET', 'POST'])
    def Register():
        email = request.form.get('email', None)
        password = request.form.get('password', None)
        passwordConfirm = request.form.get('passwordConfirm', None)
        rememberMe = request.form.get('rememberMe', False)

        if request.method == 'POST':
            if email is None:
                flash('Please provide an email address.', 'error')
            if password != passwordConfirm:
                flash('Passwords do not match.', 'error')

            existingUser = FindOne(UserClass, email=email)
            if existingUser is not None:
                flash('An account with this email already exists.')

            else:
                if passwordConfirm == password:
                    newUser = UserClass(
                        email=email,
                        passwordHash=HashIt(password),
                        authenticated=True,
                    )
                    if callable(callbackNewUserRegistered):
                        callbackNewUserRegistered()

                    return redirect('/')

            return render_template(
                registerTemplate,
                rememberMe=rememberMe,
            )

        else:
            return render_template(
                registerTemplate,
                rememberMe=rememberMe,
            )

    if forgotTemplate is None:
        templateName = 'autogen_forgot.html'
        forgotTemplate = templateName
        with open(str(TEMPLATES_PATH / templateName), mode='wt') as file:
            file.write('''
            {% extends "main.html" %}
            {% block content %}
            <div class="container">

                <form class="form-signin" method="post">
                    <h2 class="form-signin-heading">Forgot Password:</h2>
                    <br>
                    <b><i>Enter your new password twice below.</b></i>
                    <br>
                    <label for="inputEmail" class="sr-only">Email address</label>
                    <input name="email" type="email" id="inputEmail" class="form-control" placeholder="Email address" required autofocus>

                    <label for="inputPassword" class="sr-only">Password</label>
                    <input name="password" type="password" id="inputPassword" class="form-control" placeholder="Password" required>
                    
                    <label for="inputPassword" class="sr-only">Password</label>
                    <input name="passwordConfirm" type="password" id="inputPassword" class="form-control" placeholder="Password" required>
                    
                    <button class="btn btn-lg btn-primary btn-block" type="submit">Send Forgot Email</button>

                    {{messages}}

                </form>

                <a href="/">Cancel</a><br>
                <a href="/login">Sign In</a>
            </div> <!-- /container -->
            {% endblock %}
        ''')

    @app.route('/forgot', methods=['GET', 'POST'])
    def Forgot():

        if request.method == 'POST':

            if request.form.get('password', None) != request.form.get('passwordConfirm', None):
                flash('Passwords do not match.')
                return render_template(forgotTemplate)

            # send them a reset email
            ref = request.referrer
            if ref is None:
                ref = 'www.grant-miller.com'
            referrerDomainMatch = DOMAIN_RE.search(ref)
            if referrerDomainMatch is not None:
                referrerDomain = referrerDomainMatch.group(1)
            else:
                referrerDomain = 'grant-miller.com'

            frm = 'admin@' + referrerDomain
            email = request.form.get('email')
            print('forgot email=', email)

            resetToken = GetRandomID()

            if 'Signage' in app.name:
                referrerDomain = 'signage.grant-miller.com'

            resetLink = 'http://{}/reset_password/{}'.format(referrerDomain, resetToken)
            print('resetLink=', resetLink)

            user = FindOne(UserClass, email=email)
            if user is None:
                pass
            else:
                user.resetToken = resetToken
                user.tempPasswordHash = HashIt(request.form.get('password'))

            body = '''
Click here to reset your password:

Reset My Password Now

{}
            '''.format(resetLink)

            SendEmail(to=email, subject='Password Reset', body=body)
            flash('A reset link has been emailed to you.')
            return redirect('/')

        else:
            # get the users email
            return render_template(forgotTemplate)

    @app.route('/reset_password/<resetToken>')
    def ResetPassword(resetToken):
        user = FindOne(UserClass, resetToken=resetToken)
        tempHash = user.get('tempPasswordHash', None)
        if tempHash:
            user.passwordHash = tempHash
            flash('Your password has been changed.')

        return redirect('/')


def ListOfDictToJS(l):
    '''
    take in a list of dict
    return a string like """
    events: [
            {
                title: 'All Day Event2',
                start: new Date(y, m, 1)
            },
            {
                id: 999,
                title: 'Repeating Event',
                start: new Date(y, m, d-3, 16, 0),
                allDay: false,
                className: 'info'
            },
            ]
    """
    :param d:
    :return:
    '''

    string = '['

    for d in l:
        string += '{\r\n'

        d = dict(d)  # just to make sure we arent making changes to the database
        for k, v in d.items():
            if isinstance(v, str):
                string += '{}: "{}",\r\n'.format(k, v)
            elif isinstance(v, datetime.datetime):
                month = v.month - 1
                string += '{}: {},\r\n'.format(k, v.strftime('new Date(%Y, {}, %d, %H, %M)'.format(month)))
            elif isinstance(v, bool):
                string += '{}: {},\r\n'.format(k, {True: 'true', False: 'false'}.get(v))
            elif v is None:
                string += '{}: null,\r\n'.format(k, v)
            else:
                string += '{}: {},\r\n'.format(k, v)

        string += '},\r\n'

    string += ']'
    return string
