import dataset
import json
from collections import OrderedDict

# Setting this True will cause a bunch of print statements
DEBUG = False

oldPrint = print

if DEBUG is False:
    print = lambda *a, **k: None

# The DB URI used to store/read all data. By default uses sqlite
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
                try:
                    dictObj[key] = json.dumps(value)
                except:
                    pass
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

    def AfterInsert(self, *args, **kwargs):
        '''
        Override this fucntion to do something after object is inserted in database

        Example:

class Post(PersistentDictDB):

    def AfterInsert(self):
        print('14 AfterInsert() self=', self)

        user = FindOne(UserClass, id=self.get('userID'))
        print('17 user=', user)

        posts = user.get('posts', None)
        print('21 posts={}, type(posts)={}'.format(posts, type(posts)))
        if posts is None:
            posts = []
        posts.append(self.id)
        user.posts = posts

        self['username'] = user.username
        '''

    def CustomGetKey(self, key, value):
        '''
        This class supports values of type str/int/list/bool/datetime/(others supported by dataset?) only
        This method along with CustomSetKey() can be used to support other types manually

        Example:
            class Post(PersistentDictDB):

                def CustomGetKey(self, key, value):
                    if key == 'content':
                        return key, Markup(value)
                    else:
                        return key, value

        '''
        return key, value

    def CustomSetKey(self, key, value):
        '''

        :param key:
        :param value:
        :return: tuple of (newKey, newValue)
        '''
        return key, value

    def __init__(self, *args, **kwargs):
        '''

        :param args:
        :param kwargs:
        :param uniqueKeys: list of keys that cannot be duplicated in the table
        '''

        try:
            print('44 {}.__init__(args='.format(type(self).__name__), args, ' kwargs=', kwargs)
        except Exception as e:
            # if string contains an emoji get a Unicode Error
            print('44', e)

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
                # check for duplicate rows in the db
                searchResults = FindAll(type(self), **searchDict)

                duplicateExists = False
                for item in searchResults:
                    duplicateExists = True
                    # if len(searchResults) is 0, this wont happen
                    break

                if duplicateExists:
                    raise Exception(
                        'Duplicate object. searchDict={}, kwargs={}, uniqueKeys={}, searchResults={}'.format(
                            searchDict,
                            kwargs,
                            self.uniqueKeys,
                            searchResults
                        ))

            # Create the object and insert it in the database
            super().__init__(*args, **kwargs)
            InsertDB(self)

            obj = FindOne(type(self), **self)
            self['id'] = obj['id']
            obj.AfterInsert()  # Call this so the programmer can specify actions after init

        else:
            # This is called by FindOne or FindAll to re-create an object from the database
            dictObj = args[0]
            # dictObj = ConvertDictJsonValuesToNative(dictObj) # dont do this.. items will be converted as they are __getitem__-ed
            super().__init__(**dictObj)

    def _Save(self):
        UpsertDB(self, self.uniqueKeys)

    def __setitem__(self, key, value):
        print('__setitem__', key, value)

        key, value = self.CustomSetKey(key, value)

        for aType in TYPE_CONVERT_TO_JSON:
            if isinstance(value, aType):
                value = json.dumps(value)
                break

        print('82 value={}, type(value)={}'.format(value, type(value)))
        super().__setitem__(key, value)
        self._Save()

    # depricated
    # def __setattr__(self, key, value):
    #     # This allows the user to either access db rows by "obj.key" or "obj['key']"
    #     self.__setitem__(key, value)

    def __getitem__(self, key):
        print('__getitem__ self={}, key={}'.format(self, key))
        superValue = super().__getitem__(key)
        try:
            value = json.loads(superValue)
            ret = value
        except Exception as err:
            print('92 err=', err, 'return', superValue)
            ret = superValue

        _, ret = self.CustomGetKey(key, ret)
        return ret

    # Deprecated
    # def __getattr__(self, key):
    #     print('198 __getattr__(', self, key)
    #     # This allows the user to either access db rows by "obj.key" or "obj['key']"
    #     if not key.startswith('_'):
    #         return self.__getitem__(key)
    #     else:
    #         print('202 self=', self)
    #         print('204 super()=', super())
    #         super().__getattr__(key)

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
        itemsList = []
        for k, v, in self.items():
            try:
                itemsList.append(('{}={}'.format(k, v.encode())))
            except:
                itemsList.append(('{}={}'.format(k, v)))

        return '<{}: {}>'.format(
            type(self).__name__,
            ', '.join(itemsList)
        )

    def __repr__(self):
        return str(self)


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
    listOfKeysThatMustMatch += ['id']
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


def FindAllOld(objType, **k):
    '''

    :param objType:
    :param k: an empty dict like {} will return all items from table
    :return: a list of objType objects
    '''
    print('FindAll(', objType, k)

    # return iter

    limit = k.pop('_limit', None)  # should be int or None
    print('limit=', limit)

    reverse = k.pop('_reverse', False)  # bool
    print('reverse=', reverse)

    orderBy = k.pop('_orderBy', None)  # str
    print('orderBy=', orderBy)

    k = ConvertDictValuesToJson(k)
    dbName = objType.__name__
    with dataset.connect(DB_URI) as DB:
        if len(k) is 0:
            ret = DB[dbName].all()
            print('267 FindAll .all() res=', ret)

        else:
            ret = DB[dbName].find(**k)
            print('271 FindAll res=', ret)

        # do orderBy if needed
        if orderBy is not None:
            ret = sorted(ret, key=lambda item: item[orderBy])
            print('290 ret=', ret)

        # reverse results if needed
        if reverse is True:
            ret = reversed(ret)
            print('303 ret=', ret)

        # Limit results
        if limit is None:
            ret = [objType(item, doInsert=False) for item in ret]
        else:
            ret = [objType(item, doInsert=False) for index, item in enumerate(ret) if index < limit]

        print('275 ret=', ret)

        return ret


def FindAll(objType, **k):
    '''

    :param objType:
    :param k: an empty dict like {} will return all items from table
    :return: a list of objType objects
    '''
    print('FindAll(', objType, k)

    # return iter
    # https://github.com/pudo/dataset/blob/163e6554cc0b4a6e17413a2a190a18db9b5dd13c/dataset/table.py
    reverse = k.pop('_reverse', False)  # bool
    print('reverse=', reverse)

    orderBy = k.pop('_orderBy', None)  # str
    print('366 orderBy=', orderBy)

    if reverse is True:
        if orderBy is not None:
            orderBy = '-' + orderBy
        else:
            orderBy = '-id'

    k = ConvertDictValuesToJson(k)
    dbName = objType.__name__
    with dataset.connect(DB_URI) as DB:
        if len(k) is 0:
            if orderBy is not None:
                ret = DB[dbName].all(order_by=['{}'.format(orderBy)])
            else:
                ret = DB[dbName].all()
            print('267 FindAll .all() res=', ret)

        else:

            if orderBy is not None:
                print('378 orderBy=', orderBy)
                ret = DB[dbName].find(order_by=['{}'.format(orderBy)], **k)
            else:
                ret = DB[dbName].find(**k)

        ret = [objType(item, doInsert=False) for item in list(ret)]
        print('391 ret=', ret)
        return ret


def Drop(objType):
    print('Drop(', objType)
    # Drop a table
    dbName = objType.__name__
    with dataset.connect(DB_URI) as DB:
        DB[dbName].drop()
        DB.commit()


def Delete(obj):
    print('332 Delete(', obj)
    objType = type(obj)
    dbName = objType.__name__

    with dataset.connect(DB_URI) as DB:
        DB[dbName].delete(**obj)
        DB.commit()
