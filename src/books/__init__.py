from flask import Flask
from flask_mysqldb import MySQL
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()
mysql = MySQL()

from books.routes import site

def create_app(host,user,password,db,secretkey):
    app = Flask(__name__)

    app.config['MYSQL_HOST'] = host
    app.config['MYSQL_USER'] = user
    app.config['MYSQL_PASSWORD'] = password
    app.config['MYSQL_DB'] = db
    app.config['SECRET_KEY'] = secretkey
    
    mysql.init_app(app)
    bcrypt.init_app(app)

    app.register_blueprint(site)

    return app
