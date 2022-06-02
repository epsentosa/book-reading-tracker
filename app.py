from flask import Flask, redirect,render_template, url_for, request, flash
from flask_mysqldb import MySQL
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app._static_folder = "static"
bcrypt = Bcrypt(app)

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
    error = None
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        psswd_hash = bcrypt.generate_password_hash(password)
        with mysql.connection.cursor() as cursor:
            insert_query = "INSERT INTO members (full_name,email,password) VALUES (%s,%s,%s);"
            cursor.execute(insert_query,(name,email,psswd_hash))
            mysql.connection.commit()

        return redirect(url_for('home_page'))

    return render_template("register.html")

@app.route('/login',methods = ['POST','GET'])
def login_page():
    return render_template("login.html") 

if __name__ == "__main__":
    app.run(debug=True)