import os
import sys
from flask_tools import HashIt
import uuid

basedir = os.path.abspath(os.path.dirname(__file__))
print('basedir=', basedir)

# A unique hash per machine
# hash of string like '202347123401880'
uniqueHash = HashIt(uuid.getnode())


def GetConfigClass(projectName):
    platform = sys.platform
    if 'win' in platform:
        sqlURI = 'sqlite:///{}.db'.format(projectName)
    elif 'linux' in platform:
        sqlURI = 'sqlite:////{}/{}.db'.format(basedir, projectName)

    uniqueHash = HashIt(uuid.getnode())

    class Config(object):
        SECRET_KEY = os.environ.get(
            'SECRET_KEY') or 'GRANT-MILLERS-SECRET-KEY-{}'.format(uniqueHash)
        SQLALCHEMY_TRACK_MODIFICATIONS = False
        SQLALCHEMY_DATABASE_URI = sqlURI

    return Config
