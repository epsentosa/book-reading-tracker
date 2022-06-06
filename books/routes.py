from flask import Blueprint
from flask import redirect
from flask import render_template
from flask import url_for
from flask import request
from flask import flash
from flask import session
from books import bcrypt
from books import mysql
from books.forms import RegistrationForm
from books.forms import LoginForm

site = Blueprint('site',__name__,static_folder="static")

@site.route('/')
@site.route('/home')
def home_page():
    msg = 'Welcome'
    name = ''
    is_auth = False
    if "user" in session:
        is_auth = True
        msg = f"Succesfully Login for user {session['user']}"
        name = session['user']

        return render_template("home.html",msg=msg,auth=is_auth,name=name)

    return redirect(url_for('site.login_page'))

@site.route('/register',methods = ['POST','GET'])
def register_page():
    if "user" in session:
        return redirect(url_for('site.home_page'))

    form = RegistrationForm()
    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data
        password = form.password.data
        psswd_hash = bcrypt.generate_password_hash(password)
        with mysql.connection.cursor() as cursor:
            email_check = "SELECT email FROM members WHERE email = %s;"
            insert_query = "INSERT INTO members (full_name,email,password) VALUES (%s,%s,%s);"
            cursor.execute(email_check,(email,))
            is_registered = cursor.fetchone()
            if is_registered:
                flash("Email already registered.")
                return render_template("register.html",form=form)
            else:
                cursor.execute(insert_query,(name,email,psswd_hash))
                mysql.connection.commit()

        flash("Registation Successful, please login.",category='success')
        return redirect(url_for('site.login_page'))
    
    if form.errors: 
        for error in form.errors.values():
            flash(error[0])

    return render_template("register.html",form=form)

@site.route('/login',methods = ['POST','GET'])
def login_page():
    if "user" in session:
        return redirect(url_for('site.home_page'))

    form = LoginForm()
    if request.method == "POST":
        email = form.email.data
        password = form.password.data
        with mysql.connection.cursor() as cursor:
            email_check = "SELECT email FROM members WHERE email = %s;"
            password_check = "SELECT password FROM members WHERE email = %s;"
            name = "SELECT full_name FROM members WHERE email = %s;"
            cursor.execute(email_check,(email,))
            is_email = cursor.fetchone()
            if is_email:
                cursor.execute(password_check,(email,))
                password_check = cursor.fetchone()[0]
                is_password = bcrypt.check_password_hash(password_check,password)
                if is_password:
                    cursor.execute(name,(email,))
                    name = cursor.fetchone()[0]
                    session['user'] = name
                    return redirect(url_for('site.home_page'))
                flash("Wrong Password, try again")

            else:
                flash("Email Not Found, please register")
                
    return render_template("login.html",form=form)

@site.route('/logout')
def logout():
    session.pop('user',None)
    return redirect(url_for('site.home_page'))