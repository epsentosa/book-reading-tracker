from flask import Flask, redirect,render_template, url_for, request, flash
from flask_mysqldb import MySQL
from flask_bcrypt import Bcrypt
from books.forms import RegistrationForm

app = Flask(__name__)
app._static_folder = "static"
bcrypt = Bcrypt(app)

app.config['MYSQL_HOST'] = '0.0.0.0'
app.config['MYSQL_USER'] = 'eps'
app.config['MYSQL_PASSWORD'] = 'brew'
app.config['MYSQL_DB'] = 'track_books'
app.config['SECRET_KEY'] = 'topsecretkey'

mysql = MySQL(app)

@app.route('/')
@app.route('/home')
def home_page():
    return render_template("home.html")

@app.route('/register',methods = ['POST','GET'])
def register_page():
    form = RegistrationForm()
    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data
        password = form.password.data
        psswd_hash = bcrypt.generate_password_hash(password)
        with mysql.connection.cursor() as cursor:
            insert_query = "INSERT INTO members (full_name,email,password) VALUES (%s,%s,%s);"
            cursor.execute(insert_query,(name,email,psswd_hash))
            mysql.connection.commit()

        return redirect(url_for('home_page'))
    
    if form.errors: 
        for error in form.errors.values():
            flash(error[0])

    return render_template("register.html",form=form)

@app.route('/login',methods = ['POST','GET'])
def login_page():
    return render_template("login.html") 