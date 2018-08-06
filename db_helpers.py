from flask_sqlalchemy import SQLAlchemy
import datetime

DEV_MODE = False

DB = None


def SaveToTable(obj):
    '''

    :param obj: subclass of DB.Model
    :return:
    '''
    print('SaveToTable', obj)

    DB.create_all()

    DB.session.add(obj)
    DB.session.commit()


def GetFromTable(typeOf, filter=None):
    '''

    :param typeOf: subclass of DB.Model
    :param filter: dict, if None return all
    :return:
    '''

    if filter is None:  # return all results
        return typeOf.query.all()
    else:
        l = DB.session.execute(typeOf.query.filter_by(**filter))

        def Gen(l=l):
            for item in l:
                yield item

        return Gen()


def Delete(typeOf, filter):
    pass


def GetDB(flaskApp, engineURI, devMode=False):
    '''

    :param flaskApp: Flask(__name__)
    :param engineURI: 'sqlite:///test.db'
    :param devMode: boolean, when true columns can be added
    :return:
    '''
    global DB
    global DEV_MODE

    DEV_MODE = devMode

    flaskApp.config['SQLALCHEMY_DATABASE_URI'] = engineURI

    DB = SQLAlchemy(flaskApp)

    DB.create_all()

    return DB
