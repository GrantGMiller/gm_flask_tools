from persistent_dict_db import (
    SetDB_URI,
    PersistentDictDB,
    FindOne,
    FindAll,
    Drop
)

SetDB_URI('sqlite:///test.db')

class UserClass(PersistentDictDB):
    uniqueKeys = ['email']

Drop(UserClass)

print('\n\nTest creating a new class instance')
user = UserClass(email='me@website.com', name='John')
print('user=', user)
user['testKey'] = 'testValue'

print('\n\nTest FindOne')
result = FindOne(UserClass, email='me@website.com')
print('result=', result)

result['number'] = 5625475311

print('\n\nTest finding after adding a key/value')
result2 = FindOne(UserClass, email='me@website.com')
print('result2=', result2)

print('\n\nTest adding a new object with conflicting email')
try:
    userDuplicateEmail = UserClass(email='me@website.com') # this should fail
    raise Exception('Above line should have failed.')
except Exception as e:
    print('35 Exception:', e)
    userDuplicateEmail = None
print('userDuplicateEmail=', userDuplicateEmail)

print('\n\nTest creating a object, but not using setitem')
userNoSet = UserClass(email='usernoset@website.com')
print('userNoSet=', userNoSet)

print('\n\nShow the entire database')
print('FindAll(UserClass)', list(FindAll(UserClass)))
