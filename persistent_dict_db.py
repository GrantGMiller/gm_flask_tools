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
            pass

        user = UserClass(email='me@website.com', name='John')

        # Then later in your code you can call

        result = FindOne(UserClass(email='me@website.com')
        print('result=', result)
        >> user= UserClass(email='me@website.com', name='John')
    '''

    def __setitem__(self, key, value):
        print('__setitem__', key, value)
        super().__setitem__(key, value)
        UpsertDB(self, ['id'])

    def __str__(self):
        '''

        :return: string like '<PersistentDictDB: email=me@website.com, name=John>'
        '''
        itemsList = [('{}={}'.format(k, v)) for k, v, in self.items()]
        return '<{}: {}>'.format(
            type(self).__name__,
            ', '.join(itemsList)
        )


def FindOne():
    pass


def InsertDB(dictObj):
    print('InsertDB(', dictObj)
    with dataset.connect(DB_URI) as DB:
        DB[str(type(dictObj).__name__)].insert(dictObj)
        DB.commit()


def UpdateDB(dictObj, listOfKeysThatMustMatch):
    print('UpdateDB(', dictObj, listOfKeysThatMustMatch)
    with dataset.connect(DB_URI) as DB:
        DB[str(type(dictObj).__name__)].update(dictObj, listOfKeysThatMustMatch)
        DB.commit()


def UpsertDB(dictObj, listOfKeysThatMustMatch):
    print('UpsertDB(', dictObj, listOfKeysThatMustMatch)
    with dataset.connect(DB_URI) as DB:
        DB[str(type(dictObj).__name__)].upsert(dictObj, listOfKeysThatMustMatch)
        DB.commit()


def FindOne(dictObj, **k):
    print('FindOne(', dictObj, k)

    objType = type(dictObj)
    dbName = objType.__name__

    with dataset.connect(DB_URI) as DB:
        print('{}.all()='.format(dbName), list(DB[dbName].all()))

        ret = DB[dbName].find_one(**k)
        ret = objType(ret)
        print('FindOne ret=', ret)
        return ret


def FindAll(dictObj, **k):
    print('FindAll(', dictObj, k)
    dbName = type(dictObj).__name__
    with dataset.connect(DB_URI) as DB:
        ret = DB[dbName].find(**k)
        print('FindAll ret=', ret)
        return ret
