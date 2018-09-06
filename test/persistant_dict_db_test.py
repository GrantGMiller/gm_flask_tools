from persistent_dict_db import (
    SetDB_URI,
    PersistentDictDB,
    FindOne,
)

SetDB_URI('sqlite:///test.db')


class UserClass(PersistentDictDB):
    pass

# Test creating a new class
user = UserClass(email='me@website.com', name='John')
print('user=', user)
user['testKey'] = 'testValue'

# Test finding one record
result = FindOne(UserClass(email='me@website.com'))
print('result=', result)

result['number'] = 5625475311

# Test finding after adding a key/value
result2 = FindOne(UserClass(email='me@website.com'))
print('result2=', result2)