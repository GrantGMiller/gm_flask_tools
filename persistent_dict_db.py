import dataset

global DB_URI
DB_URI = None


def SetDB_URI(dburi):
    global DB_URI
    DB_URI = dburi


class PersistentDictDB(dict):
    '''
    This class saves any changes to a database.
    You should subclass this class to create a new table.

    For example:
        class UserClass(PersistentDictDB):
            uniqueKeys = ['email']

        user = UserClass(email='me@website.com', name='John')

        # Then later in your code you can call

        result = FindOne(UserClass(email='me@website.com')
        print('result=', result)
        >> user= UserClass(email='me@website.com', name='John')
    '''

    uniqueKeys = ['id']

    def __init__(self, *a, doInsert=True, **k):
        '''

        :param a:
        :param k:
        :param uniqueKeys: list of keys that cannot be duplicated in the table
        '''
        print('{}.__init__('.format(type(self).__name__), a, k)
        super().__init__(*a, **k)

        if doInsert is True:
            existing = FindAll(type(self), **k)
            if len(list(existing)) > 0:
                duplicates = FindAll(type(self), **k)
                duplicates = list(duplicates)
                raise SystemError('A record already exists in the database. \r\n{}'.format(duplicates))

            InsertDB(self)

    def _Save(self):
        UpsertDB(self, self.uniqueKeys)

    def __setitem__(self, key, value):
        print('__setitem__', key, value)
        super().__setitem__(key, value)
        self._Save()

    def __str__(self):
        '''

        :return: string like '<PersistentDictDB: email=me@website.com, name=John>'
        '''
        itemsList = [('{}={}'.format(k, v)) for k, v, in self.items()]
        return '<{}: {}>'.format(
            type(self).__name__,
            ', '.join(itemsList)
        )


def InsertDB(dictObj):
    print('InsertDB(', dictObj)
    with dataset.connect(DB_URI) as DB:
        DB[str(type(dictObj).__name__)].insert(dictObj)
        DB.commit()


def UpsertDB(dictObj, listOfKeysThatMustMatch):
    print('UpsertDB(', dictObj, listOfKeysThatMustMatch)
    with dataset.connect(DB_URI) as DB:
        DB[str(type(dictObj).__name__)].upsert(dictObj, listOfKeysThatMustMatch)
        DB.commit()


def FindOne(objType, **k):
    print('FindOne(', objType, k)

    objType
    dbName = objType.__name__

    with dataset.connect(DB_URI) as DB:
        print('{}.all()='.format(dbName), list(DB[dbName].all()))

        ret = DB[dbName].find_one(**k)
        ret = objType(ret, doInsert=False)
        print('FindOne ret=', ret)
        return ret


def FindAll(objType, **k):
    # return iter
    print('FindAll(', objType, k)
    dbName = objType.__name__
    with dataset.connect(DB_URI) as DB:
        ret = DB[dbName].find(**k)
        print('FindAll ret=', ret)
        return ret


def Drop(objType):
    print('Drop(', objType)
    # Drop a table
    dbName = objType.__name__
    with dataset.connect(DB_URI) as DB:
        DB[dbName].drop()
        DB.commit()
