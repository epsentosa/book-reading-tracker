from flask import Flask, redirect,render_template, url_for, request
from flask_mysqldb import MySQL

app = Flask(__name__)
app._static_folder = "static"

app.config['MYSQL_HOST'] = '0.0.0.0'
app.config['MYSQL_USER'] = 'eps'
app.config['MYSQL_PASSWORD'] = 'brew'
app.config['MYSQL_DB'] = 'track_books'

mysql = MySQL(app)

@app.route('/')
@app.route('/home')
def home_page():
    return render_template("home.html")

@app.route('/register',methods = ['POST','GET'])
def register_page():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        with mysql.connection as conn:
            cursor = conn.cursor()
            insert_query = "INSERT INTO members (full_name,email,password) VALUES (%s,%s,%s);"
            cursor.execute(insert_query,(name,email,password))
            conn.commit()
            return redirect('/home')

    return render_template("register.html")

@app.route('/login',methods = ['POST','GET'])
def login_page():
    return render_template("login.html") 

if __name__ == "__main__":
    app.run(debug=True)