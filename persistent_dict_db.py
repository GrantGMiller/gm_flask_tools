import dataset
import json
from collections import OrderedDict

DEBUG = True
if not DEBUG:
    print = lambda *a, **k: None

global DB_URI
DB_URI = None


def SetDB_URI(dburi):
    print('SetDB_URI(', dburi)
    global DB_URI
    DB_URI = dburi


TYPE_CONVERT_TO_JSON = [list, dict]


def ConvertDictValuesToJson(dictObj):
    for key, value in dictObj.copy().items():
        for aType in TYPE_CONVERT_TO_JSON:
            if isinstance(value, aType):
                dictObj[key] = json.dumps(value)
                break
    return dictObj


def ConvertDictJsonValuesToNative(dictObj):
    for key, value in dictObj.copy().items():
        try:
            newValue = json.loads(value)
            dictObj[key] = newValue
        except:
            pass
    return dictObj


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

    def AfterInit(self, *args, **kwargs):
        '''
        Override this fucntion to do something after object is placed in database
        :param a:
        :param k:
        :return: tuple of (args, kwargs)
        '''

    def __init__(self, *args, **kwargs):
        '''

        :param args:
        :param kwargs:
        :param uniqueKeys: list of keys that cannot be duplicated in the table
        '''
        # print('44 {}.__init__(args='.format(type(self).__name__), args, ' kwargs=', kwargs)
        #
        # if len(args) > 0 and isinstance(args[0], OrderedDict):
        #     kwargs = dict(args[0])
        #
        # superInitDict = {}
        # print('61 kwargs=', kwargs)
        # for uKey in self.uniqueKeys:
        #     print('uKey=', uKey)
        #     if uKey in kwargs:
        #         superInitDict[uKey] = kwargs[uKey]
        #
        # print('58 superInitDict=', superInitDict)
        # super().__init__(*args, **superInitDict)
        #
        # if doInsert is True:
        #     # called the first time this obj is created
        #     print('finding existing superInitDict=', superInitDict)
        #     existing = FindAll(type(self), **superInitDict)
        #     if len(list(existing)) > 0 and len(superInitDict) > 0:
        #         duplicates = FindAll(type(self), **superInitDict)
        #         duplicates = list(duplicates)
        #         raise SystemError('A record already exists in the database. \r\n{}'.format(duplicates))
        #
        #     InsertDB(self)
        #
        #     obj = FindOne(type(self), **superInitDict)
        #     print('68 obj=', obj)
        #     for k1, v1 in kwargs.items():
        #         print('70 obj={}, k1={}, v1={}'.format(obj, k1, v1))
        #         obj[k1] = v1
        #
        #     obj = FindOne(type(self), **kwargs)
        #     obj.AfterInit()

        ################################################

        print('44 {}.__init__(args='.format(type(self).__name__), args, ' kwargs=', kwargs)

        doInsert = kwargs.pop('doInsert', True)
        print('116 doInsert=', doInsert)
        if doInsert is True:
            # First check if there is already an object in database with the unique keys

            kwargs = ConvertDictValuesToJson(kwargs)
            print('119 kwargs=', kwargs)

            searchDict = dict()
            for key in self.uniqueKeys:
                if key in kwargs:
                    searchDict[key] = kwargs[key]

            if len(searchDict) > 0:
                # check for duplicates
                searchResults = FindAll(type(self), **searchDict)
                if len(searchResults) > 0:
                    raise Exception('Duplicate object. searchDict={}, kwargs={}, uniqueKeys={}, searchResults={}'.format(
                        searchDict,
                        kwargs,
                        self.uniqueKeys,
                        searchResults
                    ))

            # Create the object and insert it in the database
            super().__init__(*args, **kwargs)
            InsertDB(self)

            obj = FindOne(type(self), **self)
            obj.AfterInit()  # Call this so the programmer can specify actions after init

        else:
            # This is called by FindOne or FindAll to re-create an object from the database
            dictObj = args[0]
            #dictObj = ConvertDictJsonValuesToNative(dictObj) # dont do this.. items will be converted as they are __getitem__-ed
            super().__init__(**dictObj)

    def _Save(self):
        UpsertDB(self, self.uniqueKeys)

    def __setitem__(self, key, value):
        print('__setitem__', key, value)

        for aType in TYPE_CONVERT_TO_JSON:
            if isinstance(value, aType):
                value = json.dumps(value)
                break

        print('82 value={}, type(value)={}'.format(value, type(value)))
        super().__setitem__(key, value)
        self._Save()

    def __setattr__(self, key, value):
        # This allows the user to either access db rows by "obj.key" or "obj['key']"
        self.__setitem__(key, value)

    def __getitem__(self, key):
        print('__getitem__ self={}, key={}'.format(self, key))
        superValue = super().__getitem__(key)
        try:
            value = json.loads(superValue)
            return value
        except Exception as err:
            print('92 err=', err, 'return', superValue)
            return superValue

    def __getattr__(self, key):
        # This allows the user to either access db rows by "obj.key" or "obj['key']"
        if not key.startswith('_'):
            return self.__getitem__(key)
        else:
            super().__getattr__(key)

    def get(self, *a, **k):
        superValue = super().get(*a, **k)
        try:
            value = json.loads(superValue)
            return value
        except Exception as err:
            print('92 err=', err, 'return', superValue)
            return superValue

    def __str__(self):
        '''

        :return: string like '<PersistentDictDB: email=me@website.com, name=John>'
        '''
        itemsList = [('{}={}'.format(k, v)) for k, v, in self.items()]
        return '<{}: {}>'.format(
            type(self).__name__,
            ', '.join(itemsList)
        )


def InsertDB(obj):
    '''

    :param obj: subclass of dict()
    :return:
    '''
    print('212 InsertDB(', obj)

    tableName = type(obj).__name__
    with dataset.connect(DB_URI) as DB:
        DB[tableName].insert(obj)
        DB.commit()


def UpsertDB(obj, listOfKeysThatMustMatch):
    '''

    :param obj: subclass of dict()
    :param listOfKeysThatMustMatch:
    :return:
    '''
    print('227 UpsertDB(', obj, listOfKeysThatMustMatch)

    tableName = type(obj).__name__
    with dataset.connect(DB_URI) as DB:
        DB[tableName].upsert(obj, listOfKeysThatMustMatch)
        DB.commit()


def FindOne(objType, **k):
    k = ConvertDictValuesToJson(k)
    print('FindOne(', objType, k)

    dbName = objType.__name__

    with dataset.connect(DB_URI) as DB:
        print('242 {}.all()='.format(dbName), list(DB[dbName].all()))

        ret = DB[dbName].find_one(**k)
        print('95 FindOne ret=', ret)
        if ret is None:
            return None
        else:
            ret = objType(ret, doInsert=False)
            print('128 FindOne ret=', ret)
            return ret


def FindAll(objType, **k):
    '''

    :param objType:
    :param k: an empty dict like {} will return all items from table
    :return: a list of objType objects
    '''
    # return iter
    k = ConvertDictValuesToJson(k)
    print('FindAll(', objType, k)
    dbName = objType.__name__
    with dataset.connect(DB_URI) as DB:
        if len(k) is 0:
            res = DB[dbName].all()
            print('267 FindAll .all() res=', res)
            ret = [objType(item, doInsert=False) for item in res]
            print('269 res=', ret)
            return ret
        else:
            res = DB[dbName].find(**k)
            print('271 FindAll res=', res)
            ret = [objType(item, doInsert=False) for item in res]
            print('275 ret=', ret)
            return ret


def Drop(objType):
    print('Drop(', objType)
    # Drop a table
    dbName = objType.__name__
    with dataset.connect(DB_URI) as DB:
        DB[dbName].drop()
        DB.commit()


def Delete(obj):
    objType = type(obj)
    dbName = objType.__name__

    with dataset.connect(DB_URI) as DB:
        DB[dbName].delete(**obj)
        DB.commit()
