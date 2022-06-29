from flask import Flask
from flask_mysqldb import MySQL
from flask_bcrypt import Bcrypt
import yaml

bcrypt = Bcrypt()
mysql = MySQL()

from books.routes import site

def create_app():
    app = Flask(__name__)

    config = yaml.safe_load(open('config.yml'))
    mysql_conf = config['mysql']
    secret_key = config['secret_key']

    app.config['MYSQL_HOST'] = mysql_conf['host']
    app.config['MYSQL_USER'] = mysql_conf['user']
    app.config['MYSQL_PASSWORD'] = mysql_conf['password']
    app.config['MYSQL_DB'] = mysql_conf['db']
    app.config['SECRET_KEY'] = secret_key
    
    mysql.init_app(app)
    bcrypt.init_app(app)

    app.register_blueprint(site)

    return app
