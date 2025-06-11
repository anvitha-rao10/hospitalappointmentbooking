import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.urandom(24)
    SQLALCHEMY_DATABASE_URI = 'mysql+mysqlconnector://root:anvitha@localhost/hospitaldb'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
