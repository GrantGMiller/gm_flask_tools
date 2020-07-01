import hashlib
import io
import re
import string
from subprocess import Popen, PIPE
from email.mime.text import MIMEText
import sys
import time
import datetime
from queue import Queue
import requests
from flask import (
    Flask,
    render_template,
    session,
    request,
    redirect,
    flash,
    Markup,
    url_for,
    send_file, jsonify)
from dictabase import (
    FindOne,
    FindAll,
    BaseTable,
    RegisterDBURI,
    New,
)
import uuid
import functools
from collections import namedtuple, deque, OrderedDict, defaultdict
import os
from pathlib import Path as _PathlibPath
import traceback
import base64
import threading
import flask_apscheduler

AUTH_TOKEN_EXPIRATION_SECONDS = 60 * 60 * 24 * 365  # seconds
DOMAIN_RE = re.compile('.+\.(.+\.[^\/]+)')

DEBUG = False
if DEBUG is False or sys.platform.startswith('linux'):
    print = lambda *a, **k: None


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


def FormatPhoneNumber(phone):
    print('54 FormatPhoneNumber(', phone)
    phone = phone
    phone = str(phone)

    ret = ''

    # remove non-digits
    for ch in phone:
        if ch.isdigit() or ch == '+':
            ret += ch

    if not ret.startswith('+1'):
        ret = '+1' + ret

    print('66 ret=', ret)
    return ret


RE_PHONE_NUMBER = re.compile('\+\d{1}')


def IsValidPhone(phone):
    print('76 IsValidPhone(', phone)
    print('len(phone)=', len(phone))
    match = RE_PHONE_NUMBER.search(phone)
    print('match=', match)

    ret = match is not None and len(phone) == 12
    print('78 ret=', ret)
    return ret


def IsValidMACAddress(mac):
    if not isinstance(mac, str):
        return False

    return bool(re.match("[0-9a-f]{2}([-:]?)[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$", mac.lower()))


def IsValidHostname(hostname):
    if not isinstance(hostname, str):
        return False

    if len(hostname) > 255:
        return False
    if hostname[-1] == ".":
        hostname = hostname[:-1]  # strip exactly one dot from the right, if present
    allowed = re.compile("(?!-)[A-Z\d-]{1,63}(?<!-)$", re.IGNORECASE)
    return all(allowed.match(x) for x in hostname.split("."))


def GetRandomID(length=None):
    hash = HashIt(None)
    if length:
        return hash[:length]
    else:
        return hash


uniqueID = uuid.getnode()


def GetMachineUniqueID():
    ret = HashIt(uuid.getnode())
    print('GetMachineUniqueID( return', ret)
    return ret


def HashIt(strng=None, salt=None):
    '''
    This function takes in a string and converts it to a unique hash.
    Note: this is a one-way conversion. The value cannot be converted from hash to the original string
    :param strng: str, if None a random hash will be returned
    :return: str
    '''
    if salt is None:
        salt = GetConfigVar('SECRET_KEY')
        if salt is None:
            salt = str(uniqueID)

    if strng is None:
        # if None a random hash will be returned
        strng = uuid.uuid4()

    if not isinstance(strng, str):
        strng = str(strng)

    hash1 = hashlib.sha512(bytes(strng, 'utf-8')).hexdigest()
    hash1 += salt
    hash2 = hashlib.sha512(bytes(hash1, 'utf-8')).hexdigest()
    return hash2


def GetRandomWord():
    return requests.get('https://grant-miller.com/get_random_word').text


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


def FTSendEmail(to, frm=None, subject=None, body=None):
    '''
    linux example
    sendmail -t grant@grant-miller.com
    hello test 357
    CTRL+D

    :param to:
    :param frm:
    :param subject:
    :param body:
    :return:
    '''
    if 'win' in sys.platform:
        print('FTSendEmail(', to, frm, subject, body)
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


global _SendEmailFunction
_SendEmailFunction = FTSendEmail


def SendEmail(*a, **k):
    try:
        AddJob(_SendEmailFunction, *a, **k)
    except Exception as e:
        print('239 Exception:', e)


def RegisterEmailSender(func):
    '''
    func should accept the following parameters
    func(to=None, frm=None, cc=None, bcc=None, subject=None, body=None, html=None, attachments=None)
    '''
    print('244 RegisterEmailSender(', func, 'from', func.__module__)
    global _SendEmailFunction
    _SendEmailFunction = func


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
    '''
    Takes an index "num" and a min/max and loops is around
    for example
    ModIndexLoop(1, 1, 4) = 1
    ModIndexLoop(2, 1, 4) = 2
    ModIndexLoop(3, 1, 4) = 3
    ModIndexLoop(4, 1, 4) = 4
    ModIndexLoop(5, 1, 4) = 1
    ModIndexLoop(6, 1, 4) = 2
    :param num: int
    :param min_: int
    :param max_: int
    :return:
    '''
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


class UserClass(BaseTable):
    '''
    OTHER KEYS

    authToken - unique 512 char string
    lastAuthTokenTime - datatime.datetime that authToken was issued
    '''


global app


def GetApp(appName=None, *a, OtherAdminStuff=None, **k):
    # OtherAdminStuff should return dict that will be used to render_template for admin page
    global DB_URI
    global app

    displayableAppName = appName

    dbName = appName.replace(' ', '')
    appName = dbName.replace('.', '_')
    dbName = dbName.replace('.', '_')
    # engineURI = k.pop('DATABASE_URL', 'sqlite:///{}.db'.format(dbName))
    engineURI = GetConfigVar('DATABASE_URL')
    if engineURI is None:
        engineURI = 'sqlite:///{}.db'.format(dbName)

    RegisterDBURI(engineURI)

    devMode = k.pop('devMode', False)
    domainName = k.pop('domainName', 'grant-miller.com')

    secretKey = GetConfigVar('SECRET_KEY')
    if secretKey is None:
        secretKey = GetMachineUniqueID()

    projectPath = k.pop('projectPath', '')  # for pipenv file references within virtualenv
    global PROJECT_PATH
    PROJECT_PATH = projectPath

    app = Flask(
        appName,
        *a,
        static_folder='static',
        static_url_path='/',
        **k,
    )
    app.engineURI = engineURI
    app.config['SECRET_KEY'] = secretKey

    configClass = k.pop('configClass', None)

    app.jinja_env.globals['displayableAppName'] = displayableAppName

    app.domainName = domainName

    @app.route('/echo')
    @VerifyAdmin
    def Echo():
        d = {}
        for k in dir(request):
            if not k.startswith('_'):
                d[k] = str(getattr(request, k))

        return jsonify(d)

    # Flask-ApScheduler
    scheduler = flask_apscheduler.APScheduler()
    scheduler.init_app(app)
    # Store jobs in the database so they persist between restarts
    scheduler.scheduler.add_jobstore(
        'sqlalchemy',
        url='sqlite:///{}_jobstore.db'.format(dbName))
    scheduler.start()

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

    RegisterDBURI(DB_URI)

    @app.route(loginURL, methods=['GET', 'POST'])
    def Login(*a, **k):
        print('Login', a, k)
        email = request.form.get('email', None)
        if email is None:
            email = request.cookies.get('email', None)
        print('email=', email)

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
                    newUser = New(UserClass,
                                  email=email.lower(),
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

                    AddJob(_SendEmailFunction, to=email, frm='login@{}'.format(referrerDomain), subject='Login',
                           body=body)
                    flash('An email was sent to {}. Please click the link in the email to login.'.format(email), 'info')
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
                        'authToken', authToken,
                        expires=expireDT,
                        domain=app.domainName,
                    )
                    return resp

                else:
                    # auth token expired
                    flash('Auth Token expired. Please log in again.', 'danger')
                    return redirect(url_for(Login))

            else:
                flash('Auth Token has no expiration. This is invalid. Please log in again.', 'danger')
                return redirect(url_for(Login))

        else:
            flash('Error 348. Login Failed', 'danger')
            return render_template('login_failed.html')


def SetUser(userObj):
    session['email'] = userObj['email']


def GetUser(email=None):
    # return user object if logged in, else return None
    # if user provides an email then return that user obj
    print('GetUser(', email)

    if email:
        return FindOne(UserClass, email=email)

    email = session.get('email', None)
    authToken = request.cookies.get('authToken')

    print('258 session email=', email)
    try:
        if email is None:
            userObj = FindOne(UserClass, authToken=authToken)
        else:
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
        user['authToken'] = None


global adminEmails
adminEmails = set()


def SetAdmin(email):
    adminEmails.add(email)


def VerifyLogin(func):
    '''
    Use this decorator on view's that require a log in, it will auto redirect to login page
    :param func:
    :return:
    '''

    # print('53 VerifyLogin(', func)

    @functools.wraps(func)
    def VerifyLoginWrapper(*args, **kwargs):
        # print('VerifyLoginWrapper(', args, kwargs)
        user = GetUser()
        # print('57 user=', user)
        if user is None:
            cookieAuthToken = request.values.get('authToken', None)
            # print('495 cookieAuthToken=', cookieAuthToken)
            flash('You must be logged in for that.', 'danger')
            return redirect('/login')
        else:
            return func(*args, **kwargs)

    return VerifyLoginWrapper


def VerifyAdmin(func):
    '''
    Use this decorator on view's that require a log in, it will auto redirect to login page
    :param func:
    :return:
    '''

    # print('53 VerifyLogin(', func)

    @functools.wraps(func)
    def VerifyAdminWrapper(*args, **kwargs):
        user = GetUser()
        if user and user['email'] in adminEmails:
            return func(*args, **kwargs)
        else:
            flash('You are not an admin', 'danger')
            return redirect('/login')

    return VerifyAdminWrapper


MenuOptionClass = namedtuple('MenuOptionClass', ['title', 'url', 'active'])
global menuOptions
menuOptions = dict()


def AddMenuOption(title, url):
    global menuOptions
    menuOptions[title] = url


def RemoveMenuOption(title):
    global menuOptions
    menuOptions.pop(title, None)


def GetMenu(active=None):
    active = active or ''
    ret = []
    for title, url in menuOptions.items():
        ret.append(MenuOptionClass(title, url, active.lower() == title.lower()))
    ret.sort()
    if GetUser():
        ret.append(MenuOptionClass('Logout', '/logout', False))
    return ret


PROJECT_PATH = ''


def SetupRegisterAndLoginPageWithPassword(
        app,
        mainTemplate,  # should be like mainTemplate='main.html', all templates should be in the PROJECT_PATH/templates
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

    if loginTemplate is None:
        templateName = 'autogen_login.html'
        loginTemplate = templateName

        thisTemplatePath = PathString('templates/' + templateName)
        print('thisTemplatePath=', thisTemplatePath)
        if not os.path.exists(thisTemplatePath):
            with open(thisTemplatePath, mode='wt') as file:
                file.write('''
                {{% extends "{0}" %}}
                {{% block content %}}
                <div class="container">

                    <form class="form-signin" method="post">
                        <h2 class="form-signin-heading">Please sign in</h2>

                        <label for="inputEmail" class="sr-only">Email address</label>
                        <input name="email" type="email" id="inputEmail" class="form-control" placeholder="Email address" required autofocus>

                        <label for="inputPassword" class="sr-only">Password</label>
                        <input name="password" type="password" id="inputPassword" class="form-control" placeholder="Password" required>

                        <button class="btn btn-lg btn-primary btn-block" type="submit">Sign in</button>

                        {{{{messages}}}}

                    </form>
                <br><br>
                <a href="/register">New here? Create an account.</a><br><br>
                <a href="/forgot">Forgot Password</a>
                </div> <!-- /container -->
                {{% endblock %}}
        '''.format(mainTemplate))

    if registerTemplate is None:
        templateName = 'autogen_register.html'
        registerTemplate = templateName

        thisTemplatePath = PathString('templates/' + templateName)
        if not os.path.exists(thisTemplatePath):
            with open(thisTemplatePath, mode='wt') as file:
                file.write('''
            {{% extends "{0}" %}}
            {{% block content %}}
            <div class="container">

                <form class="form-signin" method="post">
                    <h2 class="form-signin-heading">Create a new account:</h2>

                    <label for="inputEmail" class="sr-only">Email address</label>
                    <input name="email" type="email" id="inputEmail" class="form-control" placeholder="Email address" required autofocus>

                    <label for="inputPassword" class="sr-only">Password</label>
                    <input name="password" type="password" id="inputPassword" class="form-control" placeholder="Password" required>

                    <label for="inputPassword" class="sr-only">Password</label>
                    <input name="passwordConfirm" type="password" id="inputPasswordConfirm" class="form-control" placeholder="Password" required>


                    <button class="btn btn-lg btn-primary btn-block" type="submit">Register Now</button>

                    {{{{messages}}}}

                </form>
                <br>
                <a href="/forgot">Forgot Password</a><br>
                <a href="/">Cancel</a><br>
                <a href="/login">Sign In</a>
            </div> <!-- /container -->
            {{% endblock %}}
        '''.format(mainTemplate))

    LOGIN_FAILED_FLASH_MESSAGE = 'Username and/or Password is incorrect. Please try again.'

    @app.route('/login', methods=['GET', 'POST'])
    def Login():
        if GetUser():
            return redirect('/')

        email = request.form.get('email', None)
        if email:
            email = email.lower()
        password = request.form.get('password', None)
        rememberMe = request.form.get('rememberMe', False)
        if rememberMe is not False:
            rememberMe = True

        print('email=', email)
        print('password=', HashIt(password) if password else password)
        print('rememberMe=', rememberMe)

        if request.method == 'POST':
            if password is None:
                flash('Please enter a password.', 'danger')

            if email is None:
                flash('Please enter a username.', 'danger')

            if email is not None and password is not None:
                passwordHash = HashIt(password)
                userObj = FindOne(UserClass, email=email)
                print('572 userObj=', userObj)
                if userObj is None:
                    # username not found
                    flash('Error 662:' + LOGIN_FAILED_FLASH_MESSAGE, 'danger')
                    if callable(callbackFailedLogin):
                        callbackFailedLogin()

                    return render_template(
                        loginTemplate,
                        rememberMe=rememberMe,
                    )
                else:
                    if userObj.get('passwordHash', None) == passwordHash:
                        userObj['authenticated'] = True
                        session['email'] = email

                        # login successful
                        if redirectSuccess:
                            resp = redirect(redirectSuccess)

                        else:
                            resp = redirect('/')

                        expireDT = datetime.datetime.now() + datetime.timedelta(seconds=AUTH_TOKEN_EXPIRATION_SECONDS)
                        if userObj.get('authToken', None) is None:
                            userObj['authToken'] = GetRandomID()

                        resp.set_cookie(
                            'authToken', userObj['authToken'],
                            expires=expireDT,
                            domain=app.domainName,
                        )
                        return resp

                    else:
                        # password mismatch
                        # print('userObj.get("passwordHash")=', userObj.get('passwordHash', None))
                        # print('passwordHash=', passwordHash)

                        flash(LOGIN_FAILED_FLASH_MESSAGE, 'danger')
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

    @app.route('/logout')
    def Logout():
        user = GetUser()
        if user:
            user['authenticated'] = False
        session['email'] = None

        resp = redirect('/')
        resp.delete_cookie('authToken', domain=app.domainName)
        return resp

    @app.route('/register', methods=['GET', 'POST'])
    def Register():
        email = request.form.get('email', None)
        if email:
            email = email.lower()
        password = request.form.get('password', None)
        passwordConfirm = request.form.get('passwordConfirm', None)
        rememberMe = request.form.get('rememberMe', False)

        if request.method == 'POST':
            if email is None:
                flash('Please provide an email address.', 'danger')
            if password != passwordConfirm:
                flash('Passwords do not match.', 'danger')

            existingUser = FindOne(UserClass, email=email)
            if existingUser is not None:
                flash('Error 969: Invalid Email', 'danger')

            else:
                if passwordConfirm == password:
                    newUser = New(UserClass,
                                  email=email.lower(),
                                  passwordHash=HashIt(password),
                                  authenticated=True,
                                  )
                    if callable(callbackNewUserRegistered):
                        callbackNewUserRegistered(newUser)
                    session['email'] = email
                    flash('Your account has been created. Thank you.', 'success')
                    return redirect(redirectSuccess)

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

        thisTemplatePath = PathString('templates/' + templateName)
        if not os.path.exists(thisTemplatePath):
            with open(thisTemplatePath, mode='wt') as file:
                file.write('''
            {{% extends "{0}" %}}
            {{% block content %}}
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

                    {{{{messages}}}}

                </form>

                <a href="/">Cancel</a><br>
                <a href="/login">Sign In</a>
            </div> <!-- /container -->
            {{% endblock %}}
        '''.format(mainTemplate))

    @app.route('/forgot', methods=['GET', 'POST'])
    def Forgot():

        if request.method == 'POST':
            # for item in dir(request):
            #     print(item, '=', getattr(request, item))

            if request.form.get('password', None) != request.form.get('passwordConfirm', None):
                flash('Passwords do not match.', 'danger')
                return render_template(forgotTemplate)

            # send them a reset email
            try:
                referrerDomain = request.host
            except:
                referrerDomain = app.domainName

            frm = 'admin@' + referrerDomain
            email = request.form.get('email')
            print('forgot email=', email)

            resetToken = GetRandomID()

            if 'Signage' in app.name:
                referrerDomain = 'signage.grant-miller.com'

            resetLink = '{}/reset_password/{}'.format('http://{}'.format(app.domainName) or request.host_url,
                                                      resetToken)
            print('resetLink=', resetLink)

            user = FindOne(UserClass, email=email)
            if user is None:
                pass
            else:
                user['resetToken'] = resetToken
                user['tempPasswordHash'] = HashIt(request.form.get('password'))

            body = '''
Click here to reset your password:

Reset My Password Now

{}
            '''.format(resetLink)

            AddJob(_SendEmailFunction, to=email, frm=frm, subject='Password Reset', body=body)
            flash('A reset link has been emailed to you.', 'info')
            return redirect('/')

        else:
            # get the users email
            return render_template(forgotTemplate)

    @app.route('/reset_password/<resetToken>')
    def ResetPassword(resetToken):
        user = FindOne(UserClass, resetToken=resetToken)
        if user:
            tempHash = user.get('tempPasswordHash', None)
            if tempHash:
                user['passwordHash'] = tempHash
                user['resetToken'] = None
                user['tempPasswordHash'] = None
                flash('Your password has been changed.', 'info')
        else:
            flash('(Info 847) Your password has been changed', 'success')

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


def DecodeLiteral(string):
    return string.decode(encoding='iso-8859-1')


def EncodeLiteral(string):
    return string.encode(encoding='iso-8859-1')


def GetNumOfJobs():
    return len(GetJobs())


def AddJob(callback, *args, name=None, misfire_grace_time=10, **kwargs):
    print('flask_tools.AddJob(callback={}, args={}, kwargs={})'.format(callback, args, kwargs))
    Log('AddJob', callback, args, kwargs, name)
    jobID = GetRandomID(8)
    app.apscheduler.add_job(
        id=jobID,
        name=name,
        func=callback,
        args=args,
        kwargs=kwargs,
        misfire_grace_time=misfire_grace_time,  # seconds
        trigger='date',  # needed when running on ubuntu
    )
    return jobID


def PathString(path):
    if 'win' in sys.platform:
        path = _PathlibPath(path)
        if str(path).startswith('/') or str(path).startswith('\\'):
            return str(path)[1:]
        else:
            return str(path)

    else:  # linux
        mainPath = _PathlibPath(os.path.dirname(sys.modules['__main__'].__file__)).parent

        if 'app/.heroku' in str(mainPath):
            # for heroku, note: Heroku files are ephemeral
            if str(path).startswith('/'):
                return str(path)[1:]
            else:
                return str(path)

        elif 'virtualenv' in __file__:
            # when using pipenv
            projPath = _PathlibPath(PROJECT_PATH)

            if path.startswith('/'):
                if path.startswith(projPath):
                    # path already starts with project path
                    ret = path
                else:
                    path = path[1:]
                    ret = projPath / path
            else:
                ret = projPath / path

            ret = str(ret)
            return ret

        else:
            newPath = mainPath / path
            return str(newPath)[1:]


class File:
    def __init__(self, *a, **k):
        pass


class FormFile(File):
    def __init__(self, form, key):
        self._form = form
        self._key = key
        super().__init__(form, key)

    def SaveTo(self, newPath):
        self._form[self._key].data.save(PathString(newPath))
        return SystemFile(newPath)

    @property
    def Size(self, asString=False):
        size = len(self._form[self._key].data)
        if asString:
            sizeString = '{:,} Bytes'.format(size)
            return sizeString
        else:
            return size

    @property
    def Extension(self):
        return self._form[self._key].data.filename.split('.')[-1].lower()

    def Read(self):
        return self._form[self._key].data.read()

    @property
    def Name(self):
        # returns filename like "image.jpg"
        return self._form[self._key].data.filename

    def RenderResponse(self):
        return send_file(
            io.BytesIO(self.Read()),
            mimetype='image/{}'.format(self.Extension),
            as_attachment=False,  # True will make this download as a file
            attachment_filename=self.Name
        )

    def SaveToDatabaseFile(self):
        data = self.Read()
        data = base64.b64encode(data)
        data = data.decode()

        obj = New(
            DatabaseFile,
            data=data,
            name=self.Name
        )
        return obj


class SystemFile(File):
    def __init__(self, path, data=None, mode='rt'):
        self._path = PathString(path)
        super().__init__(path)

        if data:
            with open(self._path, mode=mode) as file:
                file.write(data)

    @property
    def Size(self, asString=False):
        ''' returns num of bytes'''
        size = os.stat(PathString(self._path)).st_size
        if asString:
            sizeString = '{:,} Bytes'.format(size)
            return sizeString
        else:
            return size

    @property
    def Exists(self):
        return os.path.exists(self._path)

    @property
    def Extension(self):
        ret = _PathlibPath(self._path).suffix.split('.')[-1]
        return ret

    @property
    def Name(self):
        return _PathlibPath(self._path).name

    @property
    def Read(self):
        with open(self._path, mode='rb') as file:
            return file.read()

    def SendFile(self):
        return send_file(self._path)

    @property
    def Path(self):
        return self._path

    def MakeResponse(self, asAttachment=False):
        # print('MakeResponse self.Data=', self.Data[:50])
        typeMap = {
            'jpg': 'image',
            'png': 'image',
            'jpeg': 'image',
            'gif': 'image',

            'flv': 'video',
            'mov': 'video',
            'mp4': 'video',
            'wmv': 'video',

            'mp3': 'audio',
            'wav': 'audio',
            'm4a': 'audio',
        }
        return send_file(
            filename_or_fp=self.Path,
            mimetype='{}/{}'.format(
                typeMap.get(self.Extension.lower(), 'image'),
                self.Extension,
            ),
            as_attachment=True if typeMap.get(self.Extension.lower(), 'image') == 'video' else asAttachment,
            attachment_filename=self.Name,
            cache_timeout=1
        )


class DatabaseFile(BaseTable):
    # name (str) b64 encoded data
    # data (str) (b''.encode())

    @property
    def Data(self):
        return base64.b64decode(self['data'].encode())

    @property
    def Size(self, asString=False):
        size = len(self.Data)
        if asString:
            sizeString = '{:,} Bytes'.format(size)
            return sizeString
        else:
            return size

    @property
    def Extension(self):
        return self['name'].split('.')[-1].lower()

    def Read(self):
        return self.Data

    @property
    def Name(self):
        return self['name']

    def MakeResponse(self, asAttachment=False):
        # print('MakeResponse self.Data=', self.Data[:50])
        typeMap = {
            'jpg': 'image',
            'png': 'image',
            'jpeg': 'image',
            'gif': 'image',

            'flv': 'video',
            'mov': 'video',
            'mp4': 'video',
            'wmv': 'video',

            'mp3': 'audio',
            'wav': 'audio',
            'm4a': 'audio',
        }
        return send_file(
            io.BytesIO(self.Data),
            mimetype='{}/{}'.format(
                typeMap.get(self.Extension.lower(), 'image'),
                self.Extension,
            ),
            as_attachment=True if typeMap.get(self.Extension.lower(), 'image') == 'video' else asAttachment,
            attachment_filename=self['name'],
            cache_timeout=1
        )


def FormatTimeAgo(dt):
    utcNowDt = datetime.datetime.utcnow()
    delta = utcNowDt - dt
    if delta < datetime.timedelta(days=1):
        # less than 1 day ago
        if delta < datetime.timedelta(hours=1):
            # less than 1 hour ago, show "X minutes ago"
            if delta.total_seconds() < 60:
                return '< 1 min ago'
            else:
                minsAgo = delta.total_seconds() / 60
                minsAgo = int(minsAgo)
                return '{} min{} ago'.format(
                    minsAgo,
                    's' if minsAgo > 1 else '',
                )
        else:
            # between 1hour and 24 hours ago
            hoursAgo = delta.total_seconds() / (60 * 60)
            hoursAgo = int(hoursAgo)
            return '{} hour{} ago'.format(
                hoursAgo,
                's' if hoursAgo > 1 else '',
            )
    else:
        # more than 1 day ago
        if delta.days < 31:
            daysAgo = delta.total_seconds() / (60 * 60 * 24 * 1)
            daysAgo = int(daysAgo)
            return '{} day{} ago'.format(
                daysAgo,
                's' if daysAgo > 1 else '',
            )
        else:
            # more then 30 days ago
            months = int(delta.days / 30)
            return '{} month{} ago'.format(
                months,
                's' if months > 1 else '',
            )


def FormatNumberFriendly(num):
    if num < 1000:
        return '{}'.format(num)
    elif num < 99000:
        return '{}K'.format(round(num / 1000, 1))
    elif num < 1000000000:
        return '{}M'.format(round(num / 1000000, 1))


def FormToString(form):
    ret = Markup('<form method="POST">')

    # print('1324 ret=', ret)
    ret += form.hidden_tag()

    # print('1327 ret=', ret)
    ret += Markup('''
    <table class ="table table-dark" >''')
    # '''<tr>
    #     <td class="grantFormHeader" colspan="2">
    #     ''' + type(form).__name__ + '''
    #     </td>
    # </tr>'''
    for item in form:
        if "CSRF" not in item.label() and "Submit" not in item.label() and "Save" not in item.label():
            ret += Markup('''
            <tr>
                <td class ="grantFormLabelCell" > 
                    ''' + item.label(class_="grantFormLabel") + ''':
                </td>''')
            if "File" in item.label():
                ret += Markup('''
                <td class ="form-control" >''' + str(item) + '''</td>''')
            else:
                ret += Markup('''<td>''' + item(class_="form-control") + '''</td>''')

        ret += Markup('''</tr >''')

    ret += Markup('</table>')
    ret += Markup(form.submit(class_="btn btn-primary"))
    ret += Markup('</form>')
    # print('1349 ret=', ret)

    return Markup(ret)


def RemovePunctuation(word):
    word = ''.join(ch for ch in word if ch not in string.punctuation)
    return word


def RemoveNonLetters(word):
    return ''.join(ch for ch in word if ch in string.ascii_lowercase)


def GetConfigVar(key):
    try:
        try:
            import config
            return getattr(config, key)
        except Exception as e2:
            print('flask_tools Exception 1557:', e2)
            return os.environ.get(key, None)
    except Exception as e:
        print('flask_tools Exception 1557:', e)
        return None


def ScheduleJob(dt, callback, *args, misfire_grace_time=60, name=None, **kwargs):
    '''
    Schedule a job at a specific datetime
    :param misfire_grace_time:
    :param dt: datetime
    :param callback:
    :param args:
    :param kwargs:
    :return:
    '''
    print('SchedulJob(', dt, callback, args, kwargs)
    Log('ScheduleJob(', dt, callback, args, kwargs)
    jobID = GetRandomID(length=8)
    # https://apscheduler.readthedocs.io/en/stable/modules/schedulers/base.html#apscheduler.schedulers.base.BaseScheduler.add_job

    if dt < datetime.datetime.now():
        dt = datetime.datetime.now() + datetime.timedelta(seconds=1)

    app.apscheduler.add_job(
        id=jobID,
        func=callback,
        trigger='date',  # once at a specific datetime
        run_date=dt,
        args=args,
        kwargs=kwargs,
        misfire_grace_time=misfire_grace_time,  # seconds
        name=name,
    )
    return jobID


def ScheduleIntervalJob(
        callback,
        *args,
        startDT=None,  # None means datetime.now() + interval
        weeks=0,
        days=0,
        hours=0,
        minutes=0,
        seconds=0,
        name=None,
        **kwargs
):
    '''
    Schedule a recurring job
    :return:
    '''
    Log('ScheduleIntervalJob(', callback, args, kwargs, name, startDT)
    jobID = GetRandomID(length=8)
    # https://apscheduler.readthedocs.io/en/stable/modules/schedulers/base.html#apscheduler.schedulers.base.BaseScheduler.add_job
    app.apscheduler.add_job(
        id=jobID,
        name=name,
        func=callback,
        trigger='interval',
        start_date=startDT,
        weeks=weeks,
        days=days,
        hours=hours,
        minutes=minutes,
        seconds=seconds,
        args=args,
        kwargs=kwargs
    )
    return jobID


def GetJobs():
    return app.apscheduler.get_jobs()


def RemoveJob(jobID):
    return app.apscheduler.remove_job(jobID)


def OnExit():
    Log('OnExit')


def Log(*args):
    with open('ft.log', mode='at') as file:
        file.write(f'{datetime.datetime.now()}: {" ".join([str(a) for a in args])}\r\n')
