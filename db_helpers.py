from flask_sqlalchemy import SQLAlchemy
import sqlite3

global db
db = None

global classes
classes = {}


def GetClass(string):
    global classes
    return classes.get(string, None)


def Delete(tableName, **kwargs):
    cls = GetClass(tableName)
    cls.query.filer_by(**kwargs).delete()


def Add(tableName, **kwargs):
    global db
    cls = GetClass(tableName)
    obj = cls(**kwargs)
    db.session.add(obj)
    db.session.commit()
    return obj


def Modify(tableName, filter={}, newValues={}):
    for item in Query(tableName, **filter):
        # print('Modifying item=', item)
        for key, value in newValues.items():
            # print('key=', key, ', value=', value)
            setattr(item, key, value)
    db.session.commit()


def Query(tableName, **filters):
    global db
    cls = GetClass(tableName)
    return cls.query.filter_by(**filters).all()


def _RegisterDBClass(cls):
    global classes
    classes[cls.__name__] = cls


def RegisterApp(app):
    global db
    global classes

    db = SQLAlchemy(app)

    class User(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        email = db.Column(db.String(120), unique=True, nullable=False)
        passwordHash = db.Column(db.String(128), unique=False, nullable=False)
        emailNotifications = db.Column(db.Boolean())
        confirmed = db.Column(db.Boolean())
        confirmToken = db.Column(db.String(128), unique=False, nullable=False)

        def __repr__(self):
            return '<User %r>' % self.email

    _RegisterDBClass(User)

    # Do this after all db classes have been defined
    db.create_all()

    return db
