from books import create_app
from yaml import safe_load

config = safe_load(open('config.yml'))
mysql_conf = config['mysql']
secret_key = config['secret_key']

host_production = mysql_conf['host_production']
host_development = mysql_conf['host_development']
user = mysql_conf['user']
password = mysql_conf['password']
db = mysql_conf['db']

if __name__ == "__main__":
    app = create_app(host_development,user,password,db,secret_key)
    app.run(debug=True,host='0.0.0.0')
else:
    gunicorn_app = create_app(host_production,user,password,db,secret_key)
