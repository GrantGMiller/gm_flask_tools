import hashlib
import io
import re
import string
from subprocess import Popen, PIPE
from email.mime.text import MIMEText
import sys
import datetime
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

import uuid
import functools
from collections import namedtuple
import os
from pathlib import Path as _PathlibPath
import base64
import flask_jobs
import flask_login
import flask_dictabase

# SetDebug(True)
AUTH_TOKEN_EXPIRATION_SECONDS = 60 * 60 * 24 * 365  # seconds
DOMAIN_RE = re.compile('.+\.(.+\.[^\/]+)')

DEBUG = True
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
        AddJob(
            func=_SendEmailFunction,
            args=a,
            name='SendEmail',
            kwargs=k
        )
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


class UserClass(flask_login.UserMixin, flask_dictabase.BaseTable):
    '''
    OTHER KEYS

    authToken - unique 512 char string
    lastAuthTokenTime - datatime.datetime that authToken was issued
    '''

    def get_id(self, *a, **k):
        print('UserClass.get_id(', a, k, self)
        return self['id']

    def __str__(self):
        return flask_dictabase.BaseTable.__str__(self)


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

    app.config['DATABASE_URL'] = engineURI

    db = flask_dictabase.Dictabase(app)
    app.db = db

    flask_jobs.init_app(app)

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

    # Flask-Login
    loginManager = flask_login.LoginManager()
    loginManager.login_view = '/login'
    loginManager.init_app(app)

    @loginManager.user_loader
    def LoadUser(user_id):
        return app.db.FindOne(UserClass, id=int(user_id))

    return app


def GetUser(email=None):
    # return user object if logged in, else return None
    # if user provides an email then return that user obj
    print('GetUser(', email)
    user = flask_login.current_user
    print('GetUser user=', user)
    if user.is_authenticated is False:
        return None
    else:
        return user


def LogoutUser():
    print('LogoutUser()')
    flask_login.logout_user()


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

    return flask_login.login_required(func)


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
                <div class="column is-4 is-offset-4">
                    <h3 class="title">Login</h3>
                    <div class="box">
                        <form method="POST" >
                            <div class="field">
                                <div class="control">
                                    <input class="input is-large" type="email" name="email" placeholder="Your Email" autofocus="">
                                </div>
                            </div>
                
                            <div class="field">
                                <div class="control">
                                    <input class="input is-large" type="password" name="password" placeholder="Your Password">
                                </div>
                            </div>
                            <button class="button is-block is-info is-large is-fullwidth">Login</button>
                        </form>
                    </div>
                    <a href='/register'>New Here? Create an Account</a>
                    <br><a href='/forgot'>Forgot Password</a>
                </div>
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
            <div class="column is-4 is-offset-4">
                    <h3 class="title">Register</h3>
                    <div class="box">
                        <form method="POST">
                            <div class="field">
                                <div class="control">
                                    <input class="input is-large" type="email" name="email" placeholder="Your Email" autofocus="">
                                </div>
                            </div>
                
                            <div class="field">
                                <div class="control">
                                    <input class="input is-large" type="password" name="password" placeholder="Your Password">
                                </div>
                            </div>
                
                            <div class="field">
                                <div class="control">
                                    <input class="input is-large" type="password" name="passwordConfirm" placeholder="Confirm Password">
                                </div>
                            </div>
                            <button class="button is-block is-info is-large is-fullwidth">Sign Up</button>
                        </form>
                    </div>
                    <a href='/'>Cancel</a>
                    <br><a href='/login'>Sign In</a>
                </div>
            {{% endblock %}}
        '''.format(mainTemplate))

    LOGIN_FAILED_FLASH_MESSAGE = 'Username and/or Password is incorrect. Please try again.'

    @app.route('/login', methods=['GET', 'POST'])
    def Login():
        user = GetUser()
        if user:
            print('user already logged in, redirecting to "/"')
            return redirect('/')

        email = request.form.get('email', None)
        if email:
            email = email.lower()

        password = request.form.get('password', None)

        rememberMe = request.form.get('rememberMe', False)
        if rememberMe is not False:
            rememberMe = True

        print('email=', email)
        print('password[:10]=', str(HashIt(password) if password else password)[:10])
        print('rememberMe=', rememberMe)

        if request.method == 'POST':
            if password is None:
                flash('Please enter a password.', 'danger')

            if email is None:
                flash('Please enter a username.', 'danger')

            if email is not None and password is not None:
                passwordHash = HashIt(password)
                userObj = app.db.FindOne(UserClass, email=email)

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

                    Log(
                        f'Attempted to login. email={email}, form passwordHash[:10]={passwordHash[:10]}, userObj["passwordHash"]="{userObj["passwordHash"][:10]}..."')

                    if userObj.get('passwordHash', None) == passwordHash:
                        print('login successful')

                        flask_login.login_user(
                            userObj,
                            remember=True,
                            force=True,
                        )

                        return redirect(
                            request.args.get('next', None) or
                            redirectSuccess or
                            '/'
                        )

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

        flask_login.logout_user()

        resp = redirect('/')
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

            existingUser = app.db.FindOne(UserClass, email=email)
            if existingUser is not None:
                flash('Error 969: Invalid Email', 'danger')

            else:
                if passwordConfirm == password:
                    newUser = app.db.New(
                        UserClass,
                        email=email.lower(),
                        passwordHash=HashIt(password),
                        authenticated=True,
                    )

                    flask_login.login_user(
                        newUser,
                        remember=True,
                        force=True,
                    )

                    if callable(callbackNewUserRegistered):
                        callbackNewUserRegistered(newUser)
                    flash('Your account has been created. Thank you.', 'success')

                    return redirect(
                        request.args.get('next', None) or
                        redirectSuccess or
                        '/'
                    )

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
            <div class="column is-4 is-offset-4">
                    <h3 class="title">Forgot Password</h3>
                    <div class="box">
                        <form method="POST" >
                            <div class="field">
                                <div class="control">
                                    <input class="input is-large" type="email" name="email" placeholder="Your Email" autofocus="">
                                </div>
                            </div>
                
                            <div class="field">
                                <div class="control">
                                    <input class="input is-large" type="password" name="password" placeholder="New Password">
                                </div>
                            </div>
                
                            <div class="field">
                                <div class="control">
                                    <input class="input is-large" type="password" name="passwordConfirm" placeholder="Comfirm New Password">
                                </div>
                            </div>
                            
                            <button class="button is-block is-info is-large is-fullwidth">Reset Password</button>
                        </form>
                    </div>
                    <a href='/'>Cancel</a>
                    <br><a href='/login'>Sign In</a>
                    <br><a href='/magic_link'>Get a <i>Magic Link</i></a>
                </div>
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

            resetLink = '{}/reset_password/{}'.format(
                'http://{}'.format(app.domainName) or request.host_url,
                resetToken
            )
            print('resetLink=', resetLink)

            user = app.db.FindOne(UserClass, email=email)
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

            AddJob(
                func=_SendEmailFunction,
                name='Send Email Forgot Page',
                kwargs={
                    'to': email,
                    'frm': frm,
                    'subject': 'Password Reset',
                    'body': body,
                }
            )
            flash('A reset link has been emailed to you.', 'info')
            Log(f'Emailed reset link to {email}')
            del user  # force commit
            return redirect('/')

        else:
            # get the users email
            return render_template(forgotTemplate)

    @app.route('/reset_password/<resetToken>')
    def ResetPassword(resetToken):
        user = app.db.FindOne(UserClass, resetToken=resetToken)
        if user:
            tempHash = user.get('tempPasswordHash', None)
            if tempHash:
                user['passwordHash'] = tempHash
                user['resetToken'] = None
                user['tempPasswordHash'] = None
                flash('Your password has been changed.', 'success')
                Log(f'Password for {user["email"]} has been changed. New Hash[:10]="{tempHash[:10]}..."')
                del user  # force commit
        else:
            flash('(Info 847) Your password has been changed', 'warning')
            Log(f'token {resetToken[:10]} tried to reset pw, but no user was found with that restToken"')

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


def AddJob(*a, **k):
    return flask_jobs.AddJob(*a, **k)


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
                if path.startswith(str(projPath)):
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

        obj = app.db.New(
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


class DatabaseFile(flask_dictabase.BaseTable):
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
            print('flask_tools Exception 1237:', e2)
            return os.environ.get(key, None)
    except Exception as e:
        print('flask_tools Exception 1240:', e)
        return None


def ScheduleJob(*a, **k):
    return flask_jobs.ScheduleJob(*a, **k)


def ScheduleIntervalJob(*a, **k):
    return flask_jobs.RepeatJob(*a, **k)


def GetJobs():
    return flask_jobs.GetJobs()


def RemoveJob(jobID):
    job = flask_jobs.GetJob(jobID)
    job.Delete()


def OnExit():
    Log('OnExit')


def Log(*args):
    with open('ft.log', mode='at') as file:
        file.write(f'{datetime.datetime.now()}: {" ".join([str(a) for a in args])}\r\n')


Log('end flask_tools.__init__')
