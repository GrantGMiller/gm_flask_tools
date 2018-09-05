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


def AddNewRecord(obj):
    '''

    :param obj: subclass of DB.Model
    :return:
    '''
    print('AddNewRecord(', obj)

    DB.create_all()  # create table if missing

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

                    AddNewRecord(obj)  # now that the new column has been added, try again

                else:
                    print('57', e)
                    raise e

        elif 'has no attribute' in errorString:
            # data in database does not exists in the object
            print(errorString)

        elif 'IntegrityError' in errorString:
            # we are updating a record, not adding a new record
            print('78 obj=', obj)


def UpdateRecord(obj, newDict):
    print('UpdateRecord(', obj)
    type(obj).query.filter_by()
    obj.update(**newDict)
    DB.session.commit()


class Result:
    def __init__(self, typeOf, resultProxy):
        self._typeOf = typeOf
        self._resultProxy = resultProxy

    def __iter__(self):
        for item in self._resultProxy:
            yield self._typeOf(*item)

    def first(self):
        resultProxyList = list(self._resultProxy)
        print('resultProxyList=', resultProxyList)
        if len(resultProxyList) is 0:
            return None
        else:
            return self._typeOf(*resultProxyList[0])

    def __str__(self):
        s = '<Result object'
        items = ['\n\tIndex{}={}'.format(index, item) for index, item in enumerate(list(self))]
        for item in items:
            s += item
        s += '>\n\n'
        return s


def GetFromTable(typeOf, filter=None):
    '''

    :param typeOf: subclass of DB.Model
    :param filter: dict, if None return all
    :return: Result() object
    '''
    print('GetFromTable', typeOf, filter)
    if filter is None:  # return all results
        ret = typeOf.query.all()
        print('111 ret=', ret)
        return ret
    else:
        cmd = typeOf.query.filter_by(**filter)
        print('cmd=', cmd)

        try:
            resultProxy = DB.session.execute(cmd)
        except Exception as e:
            print('118', e)
            return Result(typeOf, [])

        # for item in dir(resultProxy):
        #     print(item,'=', help(getattr(resultProxy, item)))

        # Use these methods on resultProxy
        '''
        fetchall 
        fetchmany
        fetchone 
        first
        '''

        return Result(typeOf, resultProxy)


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
