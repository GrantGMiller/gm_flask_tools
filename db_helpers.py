'''
Example database TableClass

class PersonTableClass(DB.Model):
    ID = DB.Column(DB.Integer, primary_key=True)
    name = DB.Column(DB.String(1024))
    other = DB.Column(DB.String(1024))

    def __init__(self, name, other):
        self.name = name
        self.other = other

    def __str__(self):
        return '<PersonTableClass: name={}, other={}>'.format(self.name, self.other)


'''

from flask_sqlalchemy import SQLAlchemy
import re

DEV_MODE = False

DB = None

missingColumnRE = re.compile('no column named (\w+) ')


def InitAppDatabase(app):
    global DEV_MODE
    DEV_MODE = app.debug


def SaveToTable(obj):
    '''

    :param obj: subclass of DB.Model
    :return:
    '''
    print('SaveToTable', obj)

    DB.create_all()

    DB.session.add(obj)
    try:
        DB.session.commit()
    except Exception as e:
        DB.session.rollback()

        errorString = str(e)
        print(23, errorString)
        if 'has no column named' in errorString:
            missingColumnMatch = missingColumnRE.search(errorString)
            print('missingColumnMatch=', missingColumnMatch.group(1))
            if missingColumnMatch is not None:
                # attribute in object does not exist in database

                missingColumnName = missingColumnMatch.group(1)

                if DEV_MODE is True:
                    print('Adding a column')
                    newColumn = getattr(type(obj), missingColumnName)
                    AddColumn(obj.__table__.name, newColumn)

                    SaveToTable(obj)  # now that the new column has been added, try again

                else:
                    print('57', e)
                    raise e

        elif 'has no attribute' in str(errorString):
            # data in database does not exists in the object
            print(errorString)


def GetFromTable(typeOf, filter=None):
    '''

    :param typeOf: subclass of DB.Model
    :param filter: dict, if None return all
    :return:
    '''

    if filter is None:  # return all results
        return typeOf.query.all()
    else:
        cmd = typeOf.query.filter_by(**filter)
        print('cmd=', cmd)
        l = DB.session.execute(cmd)

        def Gen(l=l):
            for item in l:
                yield item

        return Gen()


def Delete(*a, **k):
    '''
    calling Delete(obj) will delete that object from the table

    calling Delete(typeof, filter={'Name': 'Grant'}) will delete rows that match filter

    :param a:
    :param k:
    :return:
    '''

    if len(k) == 0:
        if len(a) == 1:
            # probably calling Delete(obj)
            obj = a[0]

            DB.session.delete(obj)
            DB.session.commit()

        else:
            raise TypeError('Incorrect usage. Delete can be used like "Delete(obj)" or "Delete(typeof, filter={..})"')
    else:
        filter = k.get('filter', None)
        if filter is not None:
            typeof = a[0]

            typeof.query.filter_by(**filter).delete()
        else:
            raise TypeError('Incorrect usage. Delete can be used like "Delete(obj)" or "Delete(typeof, filter={..})"')


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

    # for item in dir(DB):
    #     print(53, item, getattr(DB, item))

    return DB


def AddColumn(table_name, column):
    '''

    :param table_name: str(tableName)
    :param column: DB.Column() obj
    :return:
    '''
    # Found on: https://stackoverflow.com/questions/7300948/add-column-to-sqlalchemy-table
    print('AddColumn', table_name, column)
    engine = DB.get_engine()
    column_name = str(column.compile(dialect=engine.dialect)).split('.')[-1]
    column_type = column.type.compile(engine.dialect)

    # print('table_name=', table_name)
    # print('column_name=', column_name)
    # print('column_type=', column_type)

    cmd = 'ALTER TABLE %s ADD COLUMN %s %s' % (table_name, column_name, column_type)
    print('cmd=', cmd)

    engine.execute(cmd)
