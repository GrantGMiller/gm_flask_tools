from db_helpers import (
    SaveToTable,
    GetFromTable,
    GetDB,
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


class PersonTable(DB.Model):
    ID = DB.Column(DB.Integer, primary_key=True)
    name = DB.Column(DB.String(1024))

    def __init__(self, name):
        self.name = name

    def __str__(self):
        return '<PersonTable: name={}>'.format(self.name)


p = PersonTable('Grant{}'.format(int(time.time())))
print(type(p))
SaveToTable(obj=p)

p2 = GetFromTable(PersonTable)#, filter={'name': 'Grant'})
print('query all=', p2)
for item in p2:
    print(42, item)

p3 =  GetFromTable(PersonTable, filter={'name': 'Grant'})
print('query filter=', list(p3))

