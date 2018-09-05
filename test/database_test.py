from simple_db import (
    AddNewRecord,
    GetFromTable,
    GetDB,
    Delete
)
from flask import Flask
import time

# try:
#     import os
#     os.remove('test.db')
#     print('removed old db')
# except:
#     pass


DB = GetDB(
    flaskApp=Flask(__name__),
    engineURI='sqlite:///test.db',
    devMode=True,
)  # allows columns/tables to be changed/added dynamically, turn this off in production


class PersonTableClass(DB.Model):
    ID = DB.Column(DB.Integer, primary_key=True)
    name = DB.Column(DB.String(1024))
    other = DB.Column(DB.String(1024))

    def __init__(self, name, other):
        self.name = name
        self.other = other

    def __str__(self):
        return '<PersonTableClass: name={}, other={}>'.format(self.name, self.other)


p = PersonTableClass(
    'Grant {}'.format(int(time.time())),
    'OtherAtt'
)
print(type(p))
AddNewRecord(obj=p)

p2 = GetFromTable(PersonTableClass)  # , filter={'name': 'Grant'})
print('query all=', p2)
for item in p2:
    print(42, item)

p3 = GetFromTable(PersonTableClass, filter={'name': 'Grant'})
print('query filter=', list(p3))

print('52 deleting first record')

p4 = GetFromTable(PersonTableClass)[0]
print('deleting =', p4)
Delete(p4)

p5 = GetFromTable(PersonTableClass)  # , filter={'name': 'Grant'})
print('60 query all=', p5)
for item in p5:
    print('62', item)

print('Deleting by filter')
p6 = GetFromTable(PersonTableClass)[0]
filter = {'name': p6.name}
print('filter=', filter)

Delete(PersonTableClass, filter=filter)

p7 = GetFromTable(PersonTableClass)  # , filter={'name': 'Grant'})
print('72 query all=', p7)
for item in p7:
    print('74', item)