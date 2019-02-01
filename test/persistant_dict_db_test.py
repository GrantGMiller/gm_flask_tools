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
    userDuplicateEmail = UserClass(email='me@website.com')  # this should fail
    raise Exception('Above line should have failed.')
except Exception as e:
    print('35 Exception:', e)
    userDuplicateEmail = None

print('userDuplicateEmail=', userDuplicateEmail)
if userDuplicateEmail is not None:
    raise Exception('Should have failed but didnt')

print('\n\nTest creating a object, but not using setitem')
userNoSet = UserClass(email='usernoset@website.com')
print('userNoSet=', userNoSet)

print('\n\nShow the entire database')
print('FindAll(UserClass)', list(FindAll(UserClass)))

# test sorting, add users out of order
userB = UserClass(email='b@b.com')
userA = UserClass(email='a@a.com')
userC = UserClass(email='c@c.com')
print('userA=', userA)
print('userB=', userB)
print('userC=', userC)

orderedUsers = FindAll(UserClass, _orderBy='email')
print('orderedUsers=')
for item in orderedUsers:
    print(item)

# test limit search
limitUsers = FindAll(UserClass, _limit=2)
print('limitUsers=')
for item in limitUsers:
    print(item)

# test order and limit
limitAndOrderUsers = FindAll(UserClass, _orderBy='email', _limit=2)
print('limitAndOrderUsers=')
for item in limitAndOrderUsers:
    print(item)


# test reverseAndOrderUsers
reverseAndOrderUsers = FindAll(UserClass, _orderBy='email', _reverse=True)
print('reverseAndOrderUsers=')
for item in reverseAndOrderUsers:
    print(item)

# test reverseUsers
reverseUsers = FindAll(UserClass, _reverse=True)
print('reverseUsers=')
for item in reverseUsers:
    print(item)